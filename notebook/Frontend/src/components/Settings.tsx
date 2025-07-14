import { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Snackbar,
} from '@mui/material';

interface Settings {
  apiKey: string;
  maxContextSize: number;
  darkMode: boolean;
  autoSave: boolean;
}

export default function Settings() {
  const [settings, setSettings] = useState<Settings>({
    apiKey: localStorage.getItem('apiKey') || '',
    maxContextSize: Number(localStorage.getItem('maxContextSize')) || 3,
    darkMode: localStorage.getItem('darkMode') === 'true',
    autoSave: localStorage.getItem('autoSave') === 'true',
  });

  const [showSuccess, setShowSuccess] = useState(false);

  const handleSave = () => {
    // Save to localStorage
    localStorage.setItem('apiKey', settings.apiKey);
    localStorage.setItem('maxContextSize', settings.maxContextSize.toString());
    localStorage.setItem('darkMode', settings.darkMode.toString());
    localStorage.setItem('autoSave', settings.autoSave.toString());

    setShowSuccess(true);
  };

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', p: 2 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          API Configuration
        </Typography>
        <TextField
          fullWidth
          label="API Key"
          type="password"
          value={settings.apiKey}
          onChange={(e) => setSettings({ ...settings, apiKey: e.target.value })}
          margin="normal"
        />
        <TextField
          fullWidth
          label="Max Context Size"
          type="number"
          value={settings.maxContextSize}
          onChange={(e) =>
            setSettings({
              ...settings,
              maxContextSize: Math.max(1, Math.min(10, Number(e.target.value))),
            })
          }
          margin="normal"
          helperText="Number of context chunks to retrieve (1-10)"
        />

        <Divider sx={{ my: 3 }} />

        <Typography variant="h6" gutterBottom>
          Interface Settings
        </Typography>
        <FormControlLabel
          control={
            <Switch
              checked={settings.darkMode}
              onChange={(e) =>
                setSettings({ ...settings, darkMode: e.target.checked })
              }
            />
          }
          label="Dark Mode"
        />
        <FormControlLabel
          control={
            <Switch
              checked={settings.autoSave}
              onChange={(e) =>
                setSettings({ ...settings, autoSave: e.target.checked })
              }
            />
          }
          label="Auto-save queries"
        />

        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleSave}
          >
            Save Settings
          </Button>
        </Box>
      </Paper>

      <Snackbar
        open={showSuccess}
        autoHideDuration={3000}
        onClose={() => setShowSuccess(false)}
      >
        <Alert severity="success" sx={{ width: '100%' }}>
          Settings saved successfully
        </Alert>
      </Snackbar>
    </Box>
  );
} 