import { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  CircularProgress,
  Divider,
  Card,
  CardContent,
} from '@mui/material';
import { Send as SendIcon } from '@mui/icons-material';
import { useMutation } from 'react-query';
import { queryDocument } from '../services/api';
import ReactMarkdown from 'react-markdown';

export default function QueryInterface() {
  const [query, setQuery] = useState('');

  const queryMutation = useMutation(
    (text: string) => queryDocument(text),
    {
      onError: (error) => {
        console.error('Query error:', error);
      },
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      queryMutation.mutate(query);
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 2 }}>
      <Typography variant="h4" gutterBottom>
        Ask Questions
      </Typography>

      <Paper
        component="form"
        onSubmit={handleSubmit}
        sx={{ p: 2, mb: 4 }}
      >
        <TextField
          fullWidth
          multiline
          rows={3}
          variant="outlined"
          placeholder="Ask a question about your documents..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={queryMutation.isLoading}
        />
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
          <Button
            variant="contained"
            color="primary"
            type="submit"
            disabled={!query.trim() || queryMutation.isLoading}
            endIcon={
              queryMutation.isLoading ? (
                <CircularProgress size={20} color="inherit" />
              ) : (
                <SendIcon />
              )
            }
          >
            Send
          </Button>
        </Box>
      </Paper>

      {queryMutation.isError && (
        <Typography color="error" sx={{ mb: 2 }}>
          Error: {queryMutation.error instanceof Error ? queryMutation.error.message : 'An error occurred'}
        </Typography>
      )}

      {queryMutation.data && (
        <Box>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Response
              </Typography>
              <ReactMarkdown>{queryMutation.data.response}</ReactMarkdown>
            </CardContent>
          </Card>

          {queryMutation.data.context.length > 0 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Context
              </Typography>
              {queryMutation.data.context.map((ctx, index) => (
                <Card key={index} sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="body2" color="textSecondary">
                      Source {index + 1}
                    </Typography>
                    <Divider sx={{ my: 1 }} />
                    <ReactMarkdown>{ctx.content}</ReactMarkdown>
                    {ctx.metadata && (
                      <Typography variant="caption" color="textSecondary">
                        Metadata: {JSON.stringify(ctx.metadata)}
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              ))}
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
} 