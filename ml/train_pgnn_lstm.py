#!/usr/bin/env python3
"""
Train PGNN-LSTM model for Madhya Pradesh groundwater forecasting.
Physics-guided architecture with geology classification and rainfall integration.
"""
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
import pickle
import os
import time
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import sys

# Add ml directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ml.models.pgnn_lstm import PGNN_LSTM, PhysicsGuidedLoss, count_parameters
from ml.models.graph_builder import prepare_graph_data


class GroundwaterDataset(Dataset):
    """PyTorch Dataset for groundwater time series."""
    
    def __init__(self, sequences, well_id_to_index, scalers=None, fit_scalers=False):
        """
        Args:
            sequences: List of sequence dicts from prepare_training_data
            well_id_to_index: Dict mapping well_id to graph node index
            scalers: Dict of MinMaxScalers per well (optional)
            fit_scalers: Whether to fit new scalers (True for train, False for test)
        """
        self.sequences = sequences
        self.well_id_to_index = well_id_to_index
        
        # Initialize or use provided scalers
        if scalers is None:
            self.scalers = {}
        else:
            self.scalers = scalers
        
        # Fit scalers if needed
        if fit_scalers:
            self._fit_scalers()
        
        # Transform sequences
        self.transformed_sequences = self._transform_sequences()
    
    def _fit_scalers(self):
        """Fit MinMaxScaler for each well based on training data."""
        print("  Fitting scalers for each well...")
        
        # Collect all water levels per well
        well_data = {}
        for seq in self.sequences:
            well_id = seq['well_id']
            if well_id not in well_data:
                well_data[well_id] = []
            well_data[well_id].extend(seq['input_wl'].tolist())
            well_data[well_id].extend(seq['target_wl'].tolist())
        
        # Fit scaler for each well
        for well_id, values in well_data.items():
            scaler = MinMaxScaler()
            scaler.fit(np.array(values).reshape(-1, 1))
            self.scalers[well_id] = scaler
        
        print(f"  ✓ Fitted {len(self.scalers)} scalers")
    
    def _transform_sequences(self):
        """Transform sequences using scalers."""
        transformed = []
        
        for seq in self.sequences:
            well_id = seq['well_id']
            
            # Skip if well not in graph
            if well_id not in self.well_id_to_index:
                continue
            
            # Skip if no scaler available
            if well_id not in self.scalers:
                continue
            
            scaler = self.scalers[well_id]
            
            # Transform input and target
            input_wl_scaled = scaler.transform(seq['input_wl'].reshape(-1, 1)).flatten()
            target_wl_scaled = scaler.transform(seq['target_wl'].reshape(-1, 1)).flatten()
            
            transformed.append({
                'well_id': well_id,
                'well_index': self.well_id_to_index[well_id],
                'input_wl': torch.FloatTensor(input_wl_scaled),
                'target_wl': torch.FloatTensor(target_wl_scaled),
                'geology_type': seq['geology_type'],
                'date': seq['date']
            })
        
        return transformed
    
    def __len__(self):
        return len(self.transformed_sequences)
    
    def __getitem__(self, idx):
        return self.transformed_sequences[idx]


def collate_fn(batch):
    """Custom collate function to handle variable-length sequences."""
    input_wl = torch.stack([item['input_wl'].unsqueeze(-1) for item in batch])
    target_wl = torch.stack([item['target_wl'] for item in batch])
    well_indices = torch.tensor([item['well_index'] for item in batch], dtype=torch.long)
    geology_types = [item['geology_type'] for item in batch]
    
    return {
        'input_wl': input_wl,
        'target_wl': target_wl,
        'well_indices': well_indices,
        'geology_types': geology_types
    }


def train_epoch(model, dataloader, criterion, optimizer, adjacency, node_features, device):
    """Train for one epoch."""
    model.train()
    epoch_loss = 0.0
    epoch_components = {'mse': 0, 'smoothness': 0, 'water_balance': 0, 'mass_conservation': 0}
    num_batches = 0
    
    for batch in dataloader:
        input_wl = batch['input_wl'].to(device)
        target_wl = batch['target_wl'].to(device)
        well_indices = batch['well_indices'].to(device)
        geology_types = batch['geology_types']
        
        # Forward pass
        optimizer.zero_grad()
        predictions = model(input_wl, node_features, adjacency, well_indices, geology_types)
        
        # Compute loss
        loss, components = criterion(predictions, target_wl)
        
        # Backward pass
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        
        # Accumulate metrics
        epoch_loss += loss.item()
        for key in epoch_components:
            epoch_components[key] += components[key]
        num_batches += 1
    
    # Average metrics
    epoch_loss /= num_batches
    for key in epoch_components:
        epoch_components[key] /= num_batches
    
    return epoch_loss, epoch_components


def validate(model, dataloader, criterion, adjacency, node_features, device):
    """Validate model."""
    model.eval()
    val_loss = 0.0
    val_components = {'mse': 0, 'smoothness': 0, 'water_balance': 0, 'mass_conservation': 0}
    num_batches = 0
    
    with torch.no_grad():
        for batch in dataloader:
            input_wl = batch['input_wl'].to(device)
            target_wl = batch['target_wl'].to(device)
            well_indices = batch['well_indices'].to(device)
            geology_types = batch['geology_types']
            
            # Forward pass
            predictions = model(input_wl, node_features, adjacency, well_indices, geology_types)
            
            # Compute loss
            loss, components = criterion(predictions, target_wl)
            
            # Accumulate metrics
            val_loss += loss.item()
            for key in val_components:
                val_components[key] += components[key]
            num_batches += 1
    
    # Average metrics
    val_loss /= num_batches
    for key in val_components:
        val_components[key] /= num_batches
    
    return val_loss, val_components


def train_model(
    model,
    train_loader,
    val_loader,
    criterion,
    optimizer,
    scheduler,
    adjacency,
    node_features,
    device,
    n_epochs=150,
    patience=25,
    save_dir='ml/artifacts'
):
    """Complete training loop with early stopping."""
    
    print("\n" + "=" * 70)
    print("Training PGNN-LSTM Model")
    print("=" * 70)
    print(f"  Epochs: up to {n_epochs}")
    print(f"  Patience: {patience}")
    print(f"  Device: {device}")
    print(f"  Parameters: {count_parameters(model):,}")
    
    os.makedirs(save_dir, exist_ok=True)
    best_val_loss = float('inf')
    patience_counter = 0
    train_history = []
    val_history = []
    
    start_time = time.time()
    
    for epoch in range(1, n_epochs + 1):
        # Train
        train_loss, train_components = train_epoch(
            model, train_loader, criterion, optimizer,
            adjacency, node_features, device
        )
        
        # Validate
        val_loss, val_components = validate(
            model, val_loader, criterion,
            adjacency, node_features, device
        )
        
        # Scheduler step
        scheduler.step()
        
        # Record history
        train_history.append(train_loss)
        val_history.append(val_loss)
        
        # Check for improvement
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            
            # Save best model
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': val_loss,
                'train_loss': train_loss
            }, os.path.join(save_dir, 'pgnn_lstm_best.pt'))
        else:
            patience_counter += 1
        
        # Print progress
        if epoch % 10 == 0 or epoch == 1:
            elapsed = (time.time() - start_time) / 60
            lr = optimizer.param_groups[0]['lr']
            print(f"  Epoch {epoch:3d} | "
                  f"Train: {train_loss:.5f} | "
                  f"Val: {val_loss:.5f} | "
                  f"Best: {best_val_loss:.5f} | "
                  f"LR: {lr:.6f} | "
                  f"Patience: {patience_counter}/{patience} | "
                  f"Time: {elapsed:.1f}min")
            print(f"           MSE: {val_components['mse']:.5f} | "
                  f"Smooth: {val_components['smoothness']:.5f} | "
                  f"WBal: {val_components['water_balance']:.5f} | "
                  f"Mass: {val_components['mass_conservation']:.5f}")
        
        # Early stopping
        if patience_counter >= patience:
            print(f"\n  Early stopping at epoch {epoch}")
            break
    
    total_time = (time.time() - start_time) / 60
    print(f"\n✓ Training complete in {total_time:.1f} minutes")
    print(f"  Best validation loss: {best_val_loss:.6f}")
    print(f"  Model saved to: {save_dir}/pgnn_lstm_best.pt")
    
    return train_history, val_history


def main():
    """Main training pipeline."""
    print("=" * 70)
    print("PGNN-LSTM Training Pipeline")
    print("Madhya Pradesh Groundwater Forecasting")
    print("=" * 70)
    
    # Configuration
    BATCH_SIZE = 32
    LEARNING_RATE = 0.001
    N_EPOCHS = 150
    PATIENCE = 25
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    print(f"\nConfiguration:")
    print(f"  Batch size: {BATCH_SIZE}")
    print(f"  Learning rate: {LEARNING_RATE}")
    print(f"  Max epochs: {N_EPOCHS}")
    print(f"  Early stopping patience: {PATIENCE}")
    print(f"  Device: {DEVICE}")
    
    # 1. Load sequences
    print("\n1. Loading training sequences...")
    with open('data/train_sequences.pkl', 'rb') as f:
        train_sequences = pickle.load(f)
    
    with open('data/test_sequences.pkl', 'rb') as f:
        test_sequences = pickle.load(f)
    
    print(f"   Training sequences: {len(train_sequences):,}")
    print(f"   Test sequences: {len(test_sequences):,}")
    
    # 2. Build graph
    print("\n2. Building spatial graph...")
    adjacency, node_features, well_id_to_index = prepare_graph_data(
        'data/wells.csv',
        k_neighbors=10
    )
    
    adjacency = adjacency.to(DEVICE)
    node_features = node_features.to(DEVICE)
    
    # 3. Create datasets
    print("\n3. Creating PyTorch datasets...")
    train_dataset = GroundwaterDataset(
        train_sequences,
        well_id_to_index,
        scalers=None,
        fit_scalers=True
    )
    
    test_dataset = GroundwaterDataset(
        test_sequences,
        well_id_to_index,
        scalers=train_dataset.scalers,
        fit_scalers=False
    )
    
    print(f"   Training samples: {len(train_dataset):,}")
    print(f"   Test samples: {len(test_dataset):,}")
    
    # 4. Create dataloaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        collate_fn=collate_fn,
        num_workers=0
    )
    
    val_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        collate_fn=collate_fn,
        num_workers=0
    )
    
    # 5. Create model
    print("\n4. Creating PGNN-LSTM model...")
    model = PGNN_LSTM(
        n_node_feat=8,
        seq_len=24,
        gcn_hidden=24,
        lstm_hidden=48,
        n_layers=2,
        horizon=12,
        dropout=0.2
    ).to(DEVICE)
    
    print(f"   ✓ Model created")
    print(f"   Parameters: {count_parameters(model):,}")
    
    # 6. Setup training
    criterion = PhysicsGuidedLoss(lambda1=0.08, lambda2=0.04, lambda3=0.02)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=100, eta_min=1e-5
    )
    
    # 7. Train
    train_history, val_history = train_model(
        model,
        train_loader,
        val_loader,
        criterion,
        optimizer,
        scheduler,
        adjacency,
        node_features,
        DEVICE,
        n_epochs=N_EPOCHS,
        patience=PATIENCE,
        save_dir='ml/artifacts'
    )
    
    # 8. Save training history
    history_df = pd.DataFrame({
        'epoch': range(1, len(train_history) + 1),
        'train_loss': train_history,
        'val_loss': val_history
    })
    history_df.to_csv('ml/artifacts/training_history.csv', index=False)
    print(f"\n✓ Training history saved to: ml/artifacts/training_history.csv")
    
    # 9. Save scalers
    with open('ml/artifacts/scalers.pkl', 'wb') as f:
        pickle.dump(train_dataset.scalers, f)
    print(f"✓ Scalers saved to: ml/artifacts/scalers.pkl")
    
    # 10. Save metadata
    metadata = {
        'num_wells': len(well_id_to_index),
        'num_train_sequences': len(train_dataset),
        'num_test_sequences': len(test_dataset),
        'well_id_to_index': well_id_to_index,
        'training_date': pd.Timestamp.now().isoformat(),
        'best_val_loss': min(val_history)
    }
    
    import json
    with open('ml/artifacts/model_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Metadata saved to: ml/artifacts/model_metadata.json")
    
    print("\n" + "=" * 70)
    print("✓ Training pipeline complete!")
    print("=" * 70)
    print(f"\nNext steps:")
    print(f"  1. Evaluate model: python ml/evaluate_pgnn_lstm.py")
    print(f"  2. Integrate into API: update backend/app/routers/forecast.py")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
