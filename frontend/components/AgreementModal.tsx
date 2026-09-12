import { useState } from 'react';

interface AgreementModalProps {
  onAccept: () => void;
}

export default function AgreementModal({ onAccept }: AgreementModalProps) {
  const [agreed, setAgreed] = useState(false);

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.7)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '20px',
      backdropFilter: 'blur(4px)',
    }}>
      <div style={{
        background: 'white',
        borderRadius: '16px',
        maxWidth: '900px',
        width: '100%',
        maxHeight: '90vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
      }}>
        {/* Header */}
        <div style={{
          padding: '32px 40px',
          borderBottom: '1px solid #e2e8f0',
          display: 'flex',
          alignItems: 'center',
          gap: '20px',
        }}>
          <img 
            src="/iiti.png" 
            alt="IIT Indore" 
            style={{ 
              height: '64px',
              width: 'auto',
            }}
          />
          <div style={{ flex: 1 }}>
            <h2 style={{
              fontSize: '28px',
              fontWeight: 800,
              color: '#0f172a',
              margin: '0 0 8px 0',
              letterSpacing: '-0.02em',
            }}>
              MP Groundwater Monitor
            </h2>
            <p style={{
              fontSize: '15px',
              color: '#64748b',
              margin: 0,
            }}>
              Terms of Use & System Information
            </p>
          </div>
        </div>

        {/* Content */}
        <div style={{
          padding: '32px 40px',
          overflowY: 'auto',
          flex: 1,
        }}>
          
          {/* Acknowledgement */}
          <section style={{ marginBottom: '32px' }}>
            <h3 style={{
              fontSize: '20px',
              fontWeight: 700,
              color: '#0f172a',
              marginBottom: '16px',
            }}>
              Acknowledgement
            </h3>
            <p style={{
              fontSize: '15px',
              color: '#475569',
              lineHeight: '1.8',
              marginBottom: '12px',
            }}>
              This system has been developed at <strong>Indian Institute of Technology, Indore</strong> under the guidance of <strong>Dr. Manish Kumar Goyal</strong> (Professor, IIT Indore), <strong>Deepak Mishra</strong> (PhD Scholar, IIT Indore), and <strong>Rudra Pratap Singh Jadon</strong> (BTech Student, IIT Indore).
            </p>
            <p style={{
              fontSize: '15px',
              color: '#475569',
              lineHeight: '1.8',
            }}>
              The groundwater monitoring data is sourced from the <strong>Central Ground Water Board (CGWB)</strong> and State Ground Water Departments of Madhya Pradesh.
            </p>
          </section>

          {/* Model Information */}
          <section style={{ marginBottom: '32px' }}>
            <h3 style={{
              fontSize: '20px',
              fontWeight: 700,
              color: '#0f172a',
              marginBottom: '16px',
            }}>
              Machine Learning Model
            </h3>
            <div style={{
              background: '#f8fafc',
              padding: '20px',
              borderRadius: '12px',
              marginBottom: '16px',
              border: '1px solid #e2e8f0',
            }}>
              <div style={{ marginBottom: '12px' }}>
                <strong style={{ color: '#0f172a', fontSize: '15px' }}>Architecture:</strong>
                <span style={{ color: '#475569', fontSize: '15px', marginLeft: '8px' }}>
                  Hybrid Position-aware Graph Neural Network (PGNN) + Long Short-Term Memory (LSTM)
                </span>
              </div>
              <div style={{ marginBottom: '12px' }}>
                <strong style={{ color: '#0f172a', fontSize: '15px' }}>Framework:</strong>
                <span style={{ color: '#475569', fontSize: '15px', marginLeft: '8px' }}>
                  PyTorch with Graph Neural Networks
                </span>
              </div>
              <div>
                <strong style={{ color: '#0f172a', fontSize: '15px' }}>Training Data:</strong>
                <span style={{ color: '#475569', fontSize: '15px', marginLeft: '8px' }}>
                  Multi-year historical groundwater level measurements from 1,082+ monitoring wells
                </span>
              </div>
            </div>
          </section>

          {/* Model Performance */}
          {/* Data Inputs & Outputs */}
          <section style={{ marginBottom: '32px' }}>
            <h3 style={{
              fontSize: '20px',
              fontWeight: 700,
              color: '#0f172a',
              marginBottom: '16px',
            }}>
              Data Inputs & Outputs
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <div>
                <h4 style={{
                  fontSize: '16px',
                  fontWeight: 600,
                  color: '#0f172a',
                  marginBottom: '12px',
                }}>
                  Input Features
                </h4>
                <ul style={{
                  listStyle: 'none',
                  padding: 0,
                  margin: 0,
                  fontSize: '14px',
                  color: '#475569',
                  lineHeight: '2',
                }}>
                  <li>• Historical water levels (monthly)</li>
                  <li>• Geographic coordinates</li>
                  <li>• Geology type (Basalt, Granite, Vindhyan)</li>
                  <li>• Aquifer characteristics</li>
                  <li>• Depth below ground level</li>
                  <li>• Spatial relationships between wells</li>
                </ul>
              </div>
              <div>
                <h4 style={{
                  fontSize: '16px',
                  fontWeight: 600,
                  color: '#0f172a',
                  marginBottom: '12px',
                }}>
                  Output Predictions
                </h4>
                <ul style={{
                  listStyle: 'none',
                  padding: 0,
                  margin: 0,
                  fontSize: '14px',
                  color: '#475569',
                  lineHeight: '2',
                }}>
                  <li>• 12-month groundwater level forecast</li>
                  <li>• 95% confidence intervals</li>
                  <li>• Trend classification (Critical/Watch/Stable)</li>
                  <li>• District-level stress assessment</li>
                  <li>• Projected decline rates</li>
                  <li>• Seasonal variation patterns</li>
                </ul>
              </div>
            </div>
          </section>

          {/* Limitations */}
          <section style={{ marginBottom: '32px' }}>
            <h3 style={{
              fontSize: '20px',
              fontWeight: 700,
              color: '#0f172a',
              marginBottom: '16px',
            }}>
              System Limitations
            </h3>
            <div style={{
              background: '#fffbeb',
              padding: '20px',
              borderRadius: '12px',
              border: '1px solid #fcd34d',
            }}>
              <ul style={{
                margin: 0,
                paddingLeft: '20px',
                fontSize: '14px',
                color: '#78350f',
                lineHeight: '1.9',
              }}>
                <li>Forecasts are based on historical patterns and may not account for unprecedented events such as extreme droughts or unusual monsoon patterns</li>
                <li>Model accuracy varies by region based on data availability and geological complexity</li>
                <li>Does not incorporate real-time factors like current rainfall, extraction rates, or recharge activities</li>
                <li>Predictions assume continuation of historical water usage patterns</li>
                <li>Spatial interpolation for custom locations has reduced accuracy compared to actual monitoring wells</li>
                <li>System is designed for planning and research purposes, not for operational decision-making without expert validation</li>
              </ul>
            </div>
          </section>

          {/* Disclaimer */}
          <section>
            <h3 style={{
              fontSize: '20px',
              fontWeight: 700,
              color: '#0f172a',
              marginBottom: '16px',
            }}>
              Important Disclaimer
            </h3>
            <div style={{
              background: '#fef2f2',
              padding: '20px',
              borderRadius: '12px',
              border: '1px solid #fecaca',
            }}>
              <p style={{
                fontSize: '14px',
                color: '#991b1b',
                lineHeight: '1.8',
                margin: 0,
              }}>
                This system provides forecasts for <strong>planning and research purposes only</strong>. Actual groundwater conditions may vary significantly due to precipitation, extraction rates, recharge patterns, geological variations, and other hydrogeological factors. The predictions should not be used as the sole basis for critical water resource management decisions. Always consult qualified hydrogeologists, water resource experts, and local authorities before implementing policies or actions based on these forecasts.
              </p>
            </div>
          </section>
        </div>

        {/* Footer */}
        <div style={{
          padding: '24px 40px',
          borderTop: '1px solid #e2e8f0',
          background: '#f8fafc',
          borderBottomLeftRadius: '16px',
          borderBottomRightRadius: '16px',
        }}>
          <label style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            marginBottom: '20px',
            cursor: 'pointer',
            userSelect: 'none',
          }}>
            <input
              type="checkbox"
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
              style={{
                width: '20px',
                height: '20px',
                cursor: 'pointer',
                accentColor: '#667eea',
              }}
            />
            <span style={{
              fontSize: '15px',
              color: '#0f172a',
              fontWeight: 500,
            }}>
              I have read and understood the system information, model limitations, and disclaimer
            </span>
          </label>
          <button
            onClick={onAccept}
            disabled={!agreed}
            style={{
              width: '100%',
              padding: '14px 24px',
              background: agreed ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : '#cbd5e1',
              color: 'white',
              border: 'none',
              borderRadius: '10px',
              fontSize: '16px',
              fontWeight: 700,
              cursor: agreed ? 'pointer' : 'not-allowed',
              transition: 'all 0.2s',
              boxShadow: agreed ? '0 4px 12px rgba(102, 126, 234, 0.4)' : 'none',
            }}
            onMouseEnter={(e) => {
              if (agreed) {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 6px 16px rgba(102, 126, 234, 0.5)';
              }
            }}
            onMouseLeave={(e) => {
              if (agreed) {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
              }
            }}
          >
            Accept & Continue to Dashboard
          </button>
        </div>
      </div>

      <style jsx>{`
        @media (max-width: 768px) {
          .modal-content {
            padding: 20px;
          }
        }
        
        /* Scrollbar styling */
        div::-webkit-scrollbar {
          width: 10px;
        }
        
        div::-webkit-scrollbar-track {
          background: #e2e8f0;
          border-radius: 10px;
        }
        
        div::-webkit-scrollbar-thumb {
          background: #94a3b8;
          border-radius: 10px;
        }
        
        div::-webkit-scrollbar-thumb:hover {
          background: #64748b;
        }
      `}</style>
    </div>
  );
}
