Installation

Prerequisites
- Python 3.11 or higher
- Git
- Modern web browser
  
Step 1: Clone the Repository
git clone https://github.com/yourusername/railway-crossing-system.git
cd railway-crossing-system

Step 2: Install Python Dependencies
pip install -r requirements.txt

Step 3: Run the Application
python api/server.py

Step 4: Access the Dashboard
Open your browser and navigate to:
http://localhost:5000

💻 Usage
Starting the System
# Run the Flask server
python api/server.py

     The system will start and show:
     ============================================
     🚂 PROFESSIONAL RAILWAY CROSSING CONTROL SYSTEM
     ============================================
    🌐 Web Interface: http://localhost:5000
    📡 API Status:    http://localhost:5000/api/system/status
    📋 Next Actions:  http://localhost:5000/api/system/next-actions
    
Using the Web Dashboard
1.Monitor Crossings: View all 4 crossings in real-time
2.Control Operations: Use manual controls for each crossing
3.Run Simulations: Start automated scenarios
4.View Diagnostics: Check system health and logs
5.Emergency Control: Use emergency override when needed
