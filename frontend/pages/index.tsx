export default function Home() {
  return (
    <>
      <style jsx global>{`
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }
        
        body {
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
        }
        
        .container {
          background: white;
          border-radius: 20px;
          box-shadow: 0 20px 60px rgba(0,0,0,0.3);
          max-width: 1200px;
          width: 100%;
          display: flex;
          overflow: hidden;
          min-height: 500px;
        }
        
        .left-section {
          flex: 0 0 40%;
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 40px;
          position: relative;
        }
        
        .mr-bean {
          width: 250px;
          height: 250px;
          border-radius: 50%;
          object-fit: cover;
          border: 8px solid white;
          box-shadow: 0 10px 30px rgba(0,0,0,0.3);
          margin-bottom: 20px;
        }
        
        .name {
          color: white;
          font-size: 28px;
          font-weight: bold;
          text-align: center;
          text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .tagline {
          color: rgba(255,255,255,0.9);
          font-size: 16px;
          text-align: center;
          margin-top: 10px;
        }
        
        .right-section {
          flex: 1;
          padding: 60px 40px;
          display: flex;
          flex-direction: column;
          justify-content: center;
        }
        
        .title {
          font-size: 36px;
          color: #1a202c;
          margin-bottom: 10px;
          font-weight: 800;
        }
        
        .subtitle {
          color: #718096;
          margin-bottom: 40px;
          font-size: 18px;
        }
        
        .projects {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }
        
        .project-card {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          padding: 30px;
          border-radius: 15px;
          color: white;
          text-decoration: none;
          transition: transform 0.3s ease, box-shadow 0.3s ease;
          box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
          display: block;
        }
        
        .project-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
        }
        
        .project-card.secondary {
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
          box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4);
        }
        
        .project-card.secondary:hover {
          box-shadow: 0 8px 25px rgba(245, 87, 108, 0.6);
        }
        
        .project-title {
          font-size: 24px;
          font-weight: 700;
          margin-bottom: 10px;
        }
        
        .project-desc {
          font-size: 14px;
          opacity: 0.95;
          line-height: 1.6;
        }
        
        .project-arrow {
          display: inline-block;
          margin-left: 10px;
          transition: margin-left 0.3s ease;
        }
        
        .project-card:hover .project-arrow {
          margin-left: 15px;
        }
        
        @media (max-width: 768px) {
          .container {
            flex-direction: column;
          }
          
          .left-section {
            flex: 0 0 auto;
            padding: 30px;
          }
          
          .mr-bean {
            width: 150px;
            height: 150px;
          }
          
          .name {
            font-size: 24px;
          }
          
          .right-section {
            padding: 40px 30px;
          }
          
          .title {
            font-size: 28px;
          }
        }
      `}</style>
      
      <div className="container">
        <div className="left-section">
          <img 
            src="https://i.pinimg.com/736x/2c/98/c9/2c98c9923f53875bd0a18e1c3608bc36.jpg" 
            alt="Mr. Bean" 
            className="mr-bean"
          />
          <div className="name">Rudra Pratap Singh Jadon</div>
          <div className="tagline">BTech Student, IIT Indore</div>
        </div>
        
        <div className="right-section">
          <h1 className="title">My Projects</h1>
          <p className="subtitle">Check out what I've been working on</p>
          
          <div className="projects">
            <a href="/mpgroundwatermonitor" className="project-card">
              <div className="project-title">
                MP Groundwater Monitor
                <span className="project-arrow">→</span>
              </div>
              <div className="project-desc">
                AI-powered groundwater level forecasting system for Madhya Pradesh using PGNN-LSTM machine learning models. Real-time monitoring and predictions for 1,200+ wells.
              </div>
            </a>
            
            <a href="https://iplwithfriends.in" className="project-card secondary">
              <div className="project-title">
                IPL With Friends
                <span className="project-arrow">→</span>
              </div>
              <div className="project-desc">
                Fantasy cricket platform for IPL enthusiasts. Create leagues, compete with friends, and enjoy the thrill of cricket predictions.
              </div>
            </a>
          </div>
        </div>
      </div>
    </>
  );
}
