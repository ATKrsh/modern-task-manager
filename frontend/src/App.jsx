import React, { useEffect, useState, useRef } from 'react';
import { Activity, Cpu, HardDrive, MemoryStick, Network, LayoutDashboard, ListTree, Settings } from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import './App.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler
);

const MAX_DATA_POINTS = 30;

const createChartData = (label, color) => ({
  labels: Array(MAX_DATA_POINTS).fill(''),
  datasets: [
    {
      label,
      data: Array(MAX_DATA_POINTS).fill(0),
      borderColor: color,
      backgroundColor: `${color}33`, // 20% opacity
      fill: true,
      tension: 0.4,
      pointRadius: 0,
    },
  ],
});

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 0 },
  plugins: { legend: { display: false }, tooltip: { enabled: false } },
  scales: {
    x: { display: false },
    y: { display: false, min: 0, max: 100 },
  },
};

function App() {
  const [activeTab, setActiveTab] = useState('performance');
  const [metrics, setMetrics] = useState(null);
  const [processes, setProcesses] = useState([]);
  
  // Ref for chart data to avoid constant re-renders breaking the chart completely
  const cpuDataRef = useRef(createChartData('CPU', '#4ade80'));
  const memDataRef = useRef(createChartData('Memory', '#a78bfa'));

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/metrics');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMetrics(data);
      
      // Update CPU chart
      const newCpuData = [...cpuDataRef.current.datasets[0].data.slice(1), data.cpu.percent];
      cpuDataRef.current.datasets[0].data = newCpuData;
      
      // Update Mem chart
      const newMemData = [...memDataRef.current.datasets[0].data.slice(1), data.memory.percent];
      memDataRef.current.datasets[0].data = newMemData;
    };

    return () => ws.close();
  }, []);

  useEffect(() => {
    if (activeTab === 'processes') {
      const fetchProcesses = async () => {
        try {
          const res = await fetch('http://localhost:8000/api/processes');
          const data = await res.json();
          setProcesses(data);
        } catch (e) {
          console.error(e);
        }
      };
      fetchProcesses();
      const interval = setInterval(fetchProcesses, 2000);
      return () => clearInterval(interval);
    }
  }, [activeTab]);

  return (
    <div className="app-container">
      <div className="sidebar">
        <div className="brand">
          <Activity size={24} color="var(--accent-color)" />
          Task Manager
        </div>
        
        <div 
          className={`nav-item ${activeTab === 'performance' ? 'active' : ''}`}
          onClick={() => setActiveTab('performance')}
        >
          <LayoutDashboard size={20} />
          Performance
        </div>
        <div 
          className={`nav-item ${activeTab === 'processes' ? 'active' : ''}`}
          onClick={() => setActiveTab('processes')}
        >
          <ListTree size={20} />
          Processes
        </div>
        
        <div style={{ flex: 1 }}></div>
        
        <div className="nav-item">
          <Settings size={20} />
          Settings
        </div>
      </div>
      
      <div className="main-content">
        <div className="header">
          <h1>{activeTab === 'performance' ? 'Performance Dashboard' : 'Processes'}</h1>
          <p>Real-time system insights</p>
        </div>

        {activeTab === 'performance' && metrics && (
          <div className="grid">
            {/* CPU Card */}
            <div className="card">
              <div className="card-header">
                <div className="card-title" style={{color: 'var(--cpu-color)'}}>
                  <Cpu size={20} /> CPU
                </div>
                <div className="card-value">{metrics.cpu.percent.toFixed(1)}%</div>
              </div>
              <div style={{color: 'var(--text-secondary)', fontSize: '0.9rem'}}>
                {metrics.cpu.freq_mhz ? (metrics.cpu.freq_mhz / 1000).toFixed(2) + ' GHz' : ''}
              </div>
              <div className="chart-container">
                <Line data={{...cpuDataRef.current}} options={chartOptions} />
              </div>
            </div>

            {/* Memory Card */}
            <div className="card">
              <div className="card-header">
                <div className="card-title" style={{color: 'var(--mem-color)'}}>
                  <MemoryStick size={20} /> Memory
                </div>
                <div className="card-value">{metrics.memory.percent.toFixed(1)}%</div>
              </div>
              <div style={{color: 'var(--text-secondary)', fontSize: '0.9rem'}}>
                {metrics.memory.used_gb} GB / {metrics.memory.total_gb} GB
              </div>
              <div className="chart-container">
                <Line data={{...memDataRef.current}} options={chartOptions} />
              </div>
            </div>

            {/* Disk Card */}
            <div className="card">
              <div className="card-header">
                <div className="card-title" style={{color: 'var(--disk-color)'}}>
                  <HardDrive size={20} /> Disk (C:)
                </div>
                <div className="card-value">{metrics.disk.percent.toFixed(1)}%</div>
              </div>
              <div style={{color: 'var(--text-secondary)', fontSize: '0.9rem'}}>
                {metrics.disk.used_gb} GB used
              </div>
              <div className="chart-container">
                {/* Static visual for disk as it changes slowly */}
                <div style={{height: '100%', display: 'flex', alignItems: 'flex-end'}}>
                   <div style={{
                     width: '100%', 
                     height: `${metrics.disk.percent}%`, 
                     background: 'var(--disk-color)',
                     opacity: 0.5,
                     borderRadius: '4px'
                   }}></div>
                </div>
              </div>
            </div>

            {/* Network Card */}
            <div className="card">
              <div className="card-header">
                <div className="card-title" style={{color: 'var(--net-color)'}}>
                  <Network size={20} /> Network
                </div>
                <div className="card-value">...</div>
              </div>
              <div style={{color: 'var(--text-secondary)', fontSize: '0.9rem'}}>
                Sent: {(metrics.network.bytes_sent / 1024 / 1024).toFixed(1)} MB
                <br/>
                Recv: {(metrics.network.bytes_recv / 1024 / 1024).toFixed(1)} MB
              </div>
            </div>
          </div>
        )}

        {activeTab === 'processes' && (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>PID</th>
                  <th>Name</th>
                  <th>CPU</th>
                  <th>Memory</th>
                </tr>
              </thead>
              <tbody>
                {processes.map(p => (
                  <tr key={p.pid}>
                    <td>{p.pid}</td>
                    <td style={{fontWeight: 500}}>{p.name}</td>
                    <td>
                      <div>{p.cpu_percent.toFixed(1)}%</div>
                      <div className="usage-bar">
                        <div className="usage-fill" style={{width: `${Math.min(p.cpu_percent, 100)}%`, background: 'var(--cpu-color)'}}></div>
                      </div>
                    </td>
                    <td>
                      <div>{p.memory_mb.toFixed(1)} MB</div>
                      <div className="usage-bar">
                        <div className="usage-fill" style={{width: `${Math.min((p.memory_mb / 16000)*100, 100)}%`, background: 'var(--mem-color)'}}></div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
