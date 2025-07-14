import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import { InsertDriveFile as FileIcon } from '@mui/icons-material';
import { uploadFile } from '../services/api';

interface UploadStatus {
  filename: string;
  status: 'pending' | 'success' | 'error';
  message?: string;
}

export default function FileUpload() {
  const [uploadStatuses, setUploadStatuses] = useState<UploadStatus[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setIsUploading(true);
    const newStatuses: UploadStatus[] = [];

    for (const file of acceptedFiles) {
      try {
        newStatuses.push({ filename: file.name, status: 'pending' });
        setUploadStatuses([...newStatuses]);

        const response = await uploadFile(file);
        
        newStatuses[newStatuses.length - 1] = {
          filename: file.name,
          status: 'success',
          message: response.message,
        };
      } catch (error) {
        newStatuses[newStatuses.length - 1] = {
          filename: file.name,
          status: 'error',
          message: error instanceof Error ? error.message : 'Upload failed',
        };
      }
      setUploadStatuses([...newStatuses]);
    }

    setIsUploading(false);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt'],
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': [
        '.docx',
      ],
      'text/csv': ['.csv'],
      'application/json': ['.json'],
      'text/markdown': ['.md'],
      'application/x-ipynb+json': ['.ipynb'],
    },
  });

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', p: 2 }}>
      <Typography variant="h4" gutterBottom>
        Upload Documents
      </Typography>
      
      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          textAlign: 'center',
          cursor: 'pointer',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'divider',
          '&:hover': {
            backgroundColor: 'action.hover',
          },
        }}
      >
        <input {...getInputProps()} />
        <Typography variant="h6" gutterBottom>
          {isDragActive
            ? 'Drop the files here...'
            : 'Drag and drop files here, or click to select files'}
        </Typography>
        <Typography variant="body2" color="textSecondary">
          Supported formats: TXT, PDF, DOCX, CSV, JSON, MD, IPYNB
        </Typography>
      </Paper>

      {isUploading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <CircularProgress />
        </Box>
      )}

      {uploadStatuses.length > 0 && (
        <List sx={{ mt: 2 }}>
          {uploadStatuses.map((status, index) => (
            <ListItem key={`${status.filename}-${index}`}>
              <ListItemIcon>
                <FileIcon />
              </ListItemIcon>
              <ListItemText
                primary={status.filename}
                secondary={status.message}
              />
              {status.status === 'pending' && <CircularProgress size={20} />}
              {status.status === 'success' && (
                <Alert severity="success" sx={{ ml: 2 }}>
                  Success
                </Alert>
              )}
              {status.status === 'error' && (
                <Alert severity="error" sx={{ ml: 2 }}>
                  Error
                </Alert>
              )}
            </ListItem>
          ))}
        </List>
      )}
    </Box>
  );
} 