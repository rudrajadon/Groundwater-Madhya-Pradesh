"""
PGNN-LSTM: Physics-Guided Graph Neural Network LSTM
Architecture for Madhya Pradesh groundwater forecasting with geology classification.

Based on the reviewed architecture with:
- 2-layer GCN for spatial patterns
- 4 geology-stratified LSTMs (Basalt/Granite/Vindhyan/Unknown)
- Temporal self-attention
- Physics-guided loss (Darcy + Water balance + Mass conservation)
"""
import torch
import torch.nn as nn


class GraphConv(nn.Module):
    """
    Simple graph convolution layer with degree normalization.
    """
    def __init__(self, in_features, out_features):
        super().__init__()
        self.W = nn.Linear(in_features, out_features, bias=True)
        self.act = nn.ELU()
    
    def forward(self, x, adj):
        """
        Args:
            x: Node features [num_nodes, in_features]
            adj: Adjacency matrix [num_nodes, num_nodes]
        Returns:
            Updated node features [num_nodes, out_features]
        """
        # Degree normalization
        deg = adj.sum(1, keepdim=True).clamp(min=1e-6)
        adj_normalized = adj / deg
        
        # Aggregate from neighbors
        aggregated = torch.mm(adj_normalized, x)
        
        # Transform and activate
        return self.act(self.W(aggregated))


class GeologyLSTM(nn.Module):
    """
    Geology-specific LSTM module with dropout.
    """
    def __init__(self, input_size, hidden_size, num_layers, dropout):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size, 
            hidden_size, 
            num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x):
        """
        Args:
            x: Input sequence [batch, seq_len, input_size]
        Returns:
            Output sequence [batch, seq_len, hidden_size]
        """
        out, _ = self.lstm(x)
        return self.dropout(out)


class PGNN_LSTM(nn.Module):
    """
    Physics-Guided Graph Neural Network LSTM for groundwater forecasting.
    
    Architecture:
    1. Two-layer GCN captures spatial relationships between wells
    2. Four geology-stratified LSTMs (Basalt/Granite/Vindhyan/Unknown)
    3. Temporal self-attention layer
    4. Forecasting head with dropout
    
    Input:
        - Water level time series: [batch, seq_len, 1]
        - Node features: [num_nodes, node_feat_dim]
        - Adjacency matrix: [num_nodes, num_nodes]
        - Well indices: [batch]
        - Geology types: [batch]
    
    Output:
        - Forecast: [batch, horizon]
    """
    def __init__(
        self,
        n_node_feat=8,
        seq_len=24,
        gcn_hidden=24,
        lstm_hidden=48,
        n_layers=2,
        horizon=12,
        dropout=0.2
    ):
        super().__init__()
        self.seq_len = seq_len
        self.horizon = horizon
        self.gcn_hidden = gcn_hidden
        self.lstm_hidden = lstm_hidden
        
        # Spatial: Two-layer graph convolution
        self.gcn1 = GraphConv(n_node_feat, gcn_hidden)
        self.gcn2 = GraphConv(gcn_hidden, gcn_hidden)
        self.gcn_norm = nn.LayerNorm(gcn_hidden)
        
        # Temporal: Geology-stratified LSTMs
        lstm_input = 1 + gcn_hidden  # water level + spatial embedding
        self.lstm_basalt = GeologyLSTM(lstm_input, lstm_hidden, n_layers, dropout)
        self.lstm_granite = GeologyLSTM(lstm_input, lstm_hidden, n_layers, dropout)
        self.lstm_vindhyan = GeologyLSTM(lstm_input, lstm_hidden, n_layers, dropout)
        self.lstm_unknown = GeologyLSTM(lstm_input, lstm_hidden, n_layers, dropout)
        
        # Temporal attention
        self.attention = nn.MultiheadAttention(
            lstm_hidden,
            num_heads=4,
            dropout=dropout,
            batch_first=True
        )
        self.attn_norm = nn.LayerNorm(lstm_hidden)
        
        # Output layers
        self.fc1 = nn.Linear(lstm_hidden, lstm_hidden // 2)
        self.fc2 = nn.Linear(lstm_hidden // 2, horizon)
        self.dropout = nn.Dropout(dropout)
        self.relu = nn.ReLU()
    
    def _get_geology_lstm(self, geology_type):
        """Map geology type to corresponding LSTM."""
        geology_map = {
            'Basalt': self.lstm_basalt,
            'Granite': self.lstm_granite,
            'Vindhyan': self.lstm_vindhyan,
            'Unknown': self.lstm_unknown
        }
        return geology_map.get(geology_type, self.lstm_unknown)
    
    def forward(self, water_level_seq, node_features, adjacency, well_indices, geology_types):
        """
        Forward pass through PGNN-LSTM.
        
        Args:
            water_level_seq: [batch, seq_len, 1] - Water level time series
            node_features: [num_nodes, n_node_feat] - Static node features
            adjacency: [num_nodes, num_nodes] - Adjacency matrix
            well_indices: [batch] - Indices of wells in this batch
            geology_types: [batch] - List of geology type strings
        
        Returns:
            forecast: [batch, horizon] - Predicted water levels
        """
        # 1. Graph convolution - capture spatial patterns
        h1 = self.gcn1(node_features, adjacency)
        h2 = self.gcn2(h1, adjacency)
        spatial_embedding = self.gcn_norm(h2)  # [num_nodes, gcn_hidden]
        
        # 2. Extract spatial embedding for wells in this batch
        batch_spatial = spatial_embedding[well_indices]  # [batch, gcn_hidden]
        
        # 3. Expand spatial embedding across time and concatenate with water levels
        batch_spatial_expanded = batch_spatial.unsqueeze(1).expand(
            -1, self.seq_len, -1
        )  # [batch, seq_len, gcn_hidden]
        
        combined_input = torch.cat(
            [water_level_seq, batch_spatial_expanded], 
            dim=-1
        )  # [batch, seq_len, 1 + gcn_hidden]
        
        # 4. Geology-stratified LSTM processing
        batch_size = combined_input.shape[0]
        lstm_output = torch.zeros(
            batch_size, self.seq_len, self.lstm_hidden,
            device=combined_input.device
        )
        
        # Group by geology type for efficient processing
        geology_groups = {}
        for i, geology in enumerate(geology_types):
            if geology not in geology_groups:
                geology_groups[geology] = []
            geology_groups[geology].append(i)
        
        # Process each geology group
        for geology, indices in geology_groups.items():
            lstm_module = self._get_geology_lstm(geology)
            group_input = combined_input[indices]
            group_output = lstm_module(group_input)
            lstm_output[indices] = group_output
        
        # 5. Temporal self-attention
        attn_output, _ = self.attention(lstm_output, lstm_output, lstm_output)
        lstm_output = self.attn_norm(lstm_output + attn_output)
        
        # 6. Take final timestep
        final_hidden = lstm_output[:, -1, :]  # [batch, lstm_hidden]
        
        # 7. Forecast head
        x = self.dropout(final_hidden)
        x = self.relu(self.fc1(x))
        forecast = self.fc2(x)  # [batch, horizon]
        
        return forecast


class PhysicsGuidedLoss(nn.Module):
    """
    Physics-informed loss function combining:
    1. Data fidelity (MSE)
    2. Darcy smoothness constraint (temporal smoothness)
    3. Water balance constraint (monsoon recharge)
    4. Mass conservation constraint (bounded values)
    
    Loss = MSE + λ1*smooth + λ2*water_balance + λ3*mass_conservation
    """
    def __init__(self, lambda1=0.08, lambda2=0.04, lambda3=0.02):
        super().__init__()
        self.lambda1 = lambda1  # Smoothness weight
        self.lambda2 = lambda2  # Water balance weight
        self.lambda3 = lambda3  # Mass conservation weight
        self.mse = nn.MSELoss()
    
    def forward(self, predictions, targets):
        """
        Compute physics-guided loss.
        
        Args:
            predictions: [batch, horizon] - Predicted water levels
            targets: [batch, horizon] - True water levels
        
        Returns:
            total_loss: Combined loss value
            loss_components: Dict with individual loss components
        """
        # 1. Data fidelity
        mse_loss = self.mse(predictions, targets)
        
        # 2. Darcy smoothness - water levels should vary smoothly in time
        if predictions.shape[1] > 1:
            temporal_diff = predictions[:, 1:] - predictions[:, :-1]
            smoothness_loss = torch.mean(temporal_diff ** 2)
        else:
            smoothness_loss = torch.tensor(0.0, device=predictions.device)
        
        # 3. Seasonal water balance
        # If forecast spans monsoon season, water levels should increase
        # Assuming months 4-8 include monsoon (Jun-Sep in 0-indexed)
        if predictions.shape[1] >= 9:
            # Compare post-monsoon (month 8) to pre-monsoon (month 4)
            monsoon_change = predictions[:, 8] - predictions[:, 4]
            # Penalize decrease (negative change means water level dropped)
            water_balance_loss = torch.clamp(-monsoon_change, min=0).mean()
        else:
            water_balance_loss = torch.tensor(0.0, device=predictions.device)
        
        # 4. Mass conservation - prevent unrealistic values
        # Typical water levels in MP: 0-100m BGL or 400-600m MSL
        # Penalize predictions that are too extreme
        mass_conservation_loss = torch.clamp(predictions.abs() - 600.0, min=0).mean()
        
        # Total loss
        total_loss = (
            mse_loss
            + self.lambda1 * smoothness_loss
            + self.lambda2 * water_balance_loss
            + self.lambda3 * mass_conservation_loss
        )
        
        # Return components for monitoring
        loss_components = {
            'mse': mse_loss.item(),
            'smoothness': smoothness_loss.item(),
            'water_balance': water_balance_loss.item(),
            'mass_conservation': mass_conservation_loss.item(),
            'total': total_loss.item()
        }
        
        return total_loss, loss_components


def count_parameters(model):
    """Count trainable parameters in model."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    # Test model creation
    print("Testing PGNN-LSTM model creation...")
    
    model = PGNN_LSTM(
        n_node_feat=8,
        seq_len=24,
        gcn_hidden=24,
        lstm_hidden=48,
        n_layers=2,
        horizon=12,
        dropout=0.2
    )
    
    print(f"✓ Model created successfully")
    print(f"  Parameters: {count_parameters(model):,}")
    
    # Test forward pass
    batch_size = 4
    num_nodes = 100
    
    water_level_seq = torch.randn(batch_size, 24, 1)
    node_features = torch.randn(num_nodes, 8)
    adjacency = torch.rand(num_nodes, num_nodes)
    well_indices = torch.randint(0, num_nodes, (batch_size,))
    geology_types = ['Basalt', 'Granite', 'Vindhyan', 'Unknown']
    
    output = model(water_level_seq, node_features, adjacency, well_indices, geology_types)
    
    print(f"✓ Forward pass successful")
    print(f"  Input shape: {water_level_seq.shape}")
    print(f"  Output shape: {output.shape}")
    
    # Test loss
    criterion = PhysicsGuidedLoss()
    targets = torch.randn(batch_size, 12)
    loss, components = criterion(output, targets)
    
    print(f"✓ Loss computation successful")
    print(f"  Total loss: {loss.item():.4f}")
    print(f"  Components: {components}")
