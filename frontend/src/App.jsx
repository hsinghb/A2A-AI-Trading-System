import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  TextField,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const App = () => {
  const [goals, setGoals] = useState({
    target_return: 0.1,
    time_horizon: '1d',
    risk_tolerance: 'moderate',
    assets: ['BTC', 'ETH'],
    strategy_type: 'momentum',
  });

  const [constraints, setConstraints] = useState({
    max_position_size: 100000,
    max_drawdown: 0.05,
    allowed_assets: ['BTC', 'ETH'],
    min_liquidity: 1000000,
    max_slippage: 0.01,
  });

  const [status, setStatus] = useState('idle');
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const ws = useRef(null);

  useEffect(() => {
    // Connect to WebSocket
    ws.current = new WebSocket('ws://localhost:8000/ws/trading');

    ws.current.onopen = () => {
      console.log('WebSocket connected');
      setStatus('connected');
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages((prev) => [...prev, data]);
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('WebSocket connection error');
    };

    ws.current.onclose = () => {
      console.log('WebSocket disconnected');
      setStatus('disconnected');
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  const handleSubmit = () => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ goals, constraints }));
      setStatus('processing');
    } else {
      setError('WebSocket not connected');
    }
  };

  const getAgentColor = (agent) => {
    const colors = {
      trigger: '#2196f3',
      expert: '#4caf50',
      risk: '#f44336',
    };
    return colors[agent] || '#757575';
  };

  const renderMessage = (message) => {
    const { type, agent, data, message: msg, timestamp } = message;
    
    return (
      <Card key={timestamp} sx={{ mb: 2, borderLeft: `4px solid ${getAgentColor(agent)}` }}>
        <CardContent>
          <Typography variant="subtitle2" color="text.secondary">
            {agent?.toUpperCase()} Agent - {new Date(timestamp).toLocaleTimeString()}
          </Typography>
          {type === 'status' ? (
            <Typography>{msg}</Typography>
          ) : (
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
              {JSON.stringify(data || msg, null, 2)}
            </pre>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        AI Trading System
      </Typography>

      <Grid container spacing={3}>
        {/* Input Form */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Trading Parameters
            </Typography>
            
            <Box component="form" sx={{ mt: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Goals
              </Typography>
              <TextField
                fullWidth
                label="Target Return"
                type="number"
                value={goals.target_return}
                onChange={(e) => setGoals({ ...goals, target_return: parseFloat(e.target.value) })}
                margin="normal"
              />
              <TextField
                fullWidth
                label="Time Horizon"
                value={goals.time_horizon}
                onChange={(e) => setGoals({ ...goals, time_horizon: e.target.value })}
                margin="normal"
              />
              <TextField
                fullWidth
                label="Risk Tolerance"
                value={goals.risk_tolerance}
                onChange={(e) => setGoals({ ...goals, risk_tolerance: e.target.value })}
                margin="normal"
              />

              <Typography variant="subtitle1" sx={{ mt: 2 }} gutterBottom>
                Constraints
              </Typography>
              <TextField
                fullWidth
                label="Max Position Size"
                type="number"
                value={constraints.max_position_size}
                onChange={(e) => setConstraints({ ...constraints, max_position_size: parseFloat(e.target.value) })}
                margin="normal"
              />
              <TextField
                fullWidth
                label="Max Drawdown"
                type="number"
                value={constraints.max_drawdown}
                onChange={(e) => setConstraints({ ...constraints, max_drawdown: parseFloat(e.target.value) })}
                margin="normal"
              />
              <TextField
                fullWidth
                label="Min Liquidity"
                type="number"
                value={constraints.min_liquidity}
                onChange={(e) => setConstraints({ ...constraints, min_liquidity: parseFloat(e.target.value) })}
                margin="normal"
              />

              <Button
                fullWidth
                variant="contained"
                onClick={handleSubmit}
                disabled={status === 'processing'}
                sx={{ mt: 2 }}
              >
                {status === 'processing' ? (
                  <>
                    <CircularProgress size={24} sx={{ mr: 1 }} />
                    Processing...
                  </>
                ) : (
                  'Submit Trading Request'
                )}
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Messages and Status */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, height: '70vh', overflow: 'auto' }}>
            <Typography variant="h6" gutterBottom>
              Agent Communication
            </Typography>
            {messages.map(renderMessage)}
          </Paper>
        </Grid>
      </Grid>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default App; 