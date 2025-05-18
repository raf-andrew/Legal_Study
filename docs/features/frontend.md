# Frontend Guide

This guide explains the frontend system in the Legal Study Platform.

## Overview

The platform implements a modern frontend system with support for:

- React components
- State management
- Routing
- API integration
- UI/UX design
- Testing

## React Components

### 1. Component Structure

```typescript
// src/components/Document/DocumentList.tsx
import React from 'react';
import { useDocuments } from '../../hooks/useDocuments';
import { DocumentCard } from './DocumentCard';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorMessage } from '../common/ErrorMessage';

interface DocumentListProps {
  filter?: string;
  sortBy?: 'title' | 'createdAt' | 'updatedAt';
}

export const DocumentList: React.FC<DocumentListProps> = ({
  filter,
  sortBy = 'createdAt'
}) => {
  const { documents, loading, error } = useDocuments(filter, sortBy);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div className="document-list">
      {documents.map(document => (
        <DocumentCard
          key={document.id}
          document={document}
        />
      ))}
    </div>
  );
};
```

### 2. Custom Hooks

```typescript
// src/hooks/useDocuments.ts
import { useState, useEffect } from 'react';
import { useApi } from './useApi';
import { Document } from '../../types';

export const useDocuments = (filter?: string, sortBy?: string) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const api = useApi();

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        setLoading(true);
        const response = await api.get('/documents', {
          params: { filter, sortBy }
        });
        setDocuments(response.data);
        setError(null);
      } catch (err) {
        setError('Failed to fetch documents');
      } finally {
        setLoading(false);
      }
    };

    fetchDocuments();
  }, [filter, sortBy]);

  return { documents, loading, error };
};
```

## State Management

### 1. Redux Store

```typescript
// src/store/index.ts
import { configureStore } from '@reduxjs/toolkit';
import documentsReducer from './slices/documentsSlice';
import authReducer from './slices/authSlice';
import uiReducer from './slices/uiSlice';

export const store = configureStore({
  reducer: {
    documents: documentsReducer,
    auth: authReducer,
    ui: uiReducer
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false
    })
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

### 2. Redux Slices

```typescript
// src/store/slices/documentsSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { Document } from '../../types';
import { api } from '../../services/api';

interface DocumentsState {
  items: Document[];
  loading: boolean;
  error: string | null;
}

const initialState: DocumentsState = {
  items: [],
  loading: false,
  error: null
};

export const fetchDocuments = createAsyncThunk(
  'documents/fetchDocuments',
  async () => {
    const response = await api.get('/documents');
    return response.data;
  }
);

const documentsSlice = createSlice({
  name: 'documents',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchDocuments.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDocuments.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(fetchDocuments.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch documents';
      });
  }
});

export default documentsSlice.reducer;
```

## Routing

### 1. Route Configuration

```typescript
// src/routes/index.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { PrivateRoute } from './PrivateRoute';
import { Layout } from '../components/Layout';
import { Home } from '../pages/Home';
import { Documents } from '../pages/Documents';
import { DocumentDetail } from '../pages/DocumentDetail';
import { Login } from '../pages/Login';
import { NotFound } from '../pages/NotFound';

export const AppRoutes = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="login" element={<Login />} />
          <Route
            path="documents"
            element={
              <PrivateRoute>
                <Documents />
              </PrivateRoute>
            }
          />
          <Route
            path="documents/:id"
            element={
              <PrivateRoute>
                <DocumentDetail />
              </PrivateRoute>
            }
          />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};
```

### 2. Route Guards

```typescript
// src/routes/PrivateRoute.tsx
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

interface PrivateRouteProps {
  children: React.ReactNode;
}

export const PrivateRoute: React.FC<PrivateRouteProps> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};
```

## API Integration

### 1. API Client

```typescript
// src/services/api.ts
import axios from 'axios';
import { store } from '../store';
import { logout } from '../store/slices/authSlice';

export const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

api.interceptors.request.use(
  (config) => {
    const token = store.getState().auth.token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      store.dispatch(logout());
    }
    return Promise.reject(error);
  }
);
```

### 2. API Hooks

```typescript
// src/hooks/useApi.ts
import { useCallback } from 'react';
import { api } from '../services/api';
import { useDispatch } from 'react-redux';
import { setError } from '../store/slices/uiSlice';

export const useApi = () => {
  const dispatch = useDispatch();

  const handleRequest = useCallback(async (request: () => Promise<any>) => {
    try {
      return await request();
    } catch (error) {
      const message = error.response?.data?.message || 'An error occurred';
      dispatch(setError(message));
      throw error;
    }
  }, [dispatch]);

  return {
    get: (url: string, config = {}) =>
      handleRequest(() => api.get(url, config)),
    post: (url: string, data = {}, config = {}) =>
      handleRequest(() => api.post(url, data, config)),
    put: (url: string, data = {}, config = {}) =>
      handleRequest(() => api.put(url, data, config)),
    delete: (url: string, config = {}) =>
      handleRequest(() => api.delete(url, config))
  };
};
```

## UI/UX Design

### 1. Theme Configuration

```typescript
// src/theme/index.ts
import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0'
    },
    secondary: {
      main: '#9c27b0',
      light: '#ba68c8',
      dark: '#7b1fa2'
    }
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 500
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500
    }
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8
        }
      }
    }
  }
});
```

### 2. Styled Components

```typescript
// src/components/common/StyledComponents.ts
import styled from '@emotion/styled';
import { Paper, Button } from '@mui/material';

export const Card = styled(Paper)`
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

export const PrimaryButton = styled(Button)`
  background-color: ${props => props.theme.palette.primary.main};
  color: white;
  padding: 8px 16px;
  &:hover {
    background-color: ${props => props.theme.palette.primary.dark};
  }
`;

export const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px;
`;
```

## Testing

### 1. Component Tests

```typescript
// src/components/Document/__tests__/DocumentList.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { DocumentList } from '../DocumentList';
import { useDocuments } from '../../../hooks/useDocuments';

jest.mock('../../../hooks/useDocuments');

describe('DocumentList', () => {
  const mockDocuments = [
    { id: 1, title: 'Document 1' },
    { id: 2, title: 'Document 2' }
  ];

  beforeEach(() => {
    (useDocuments as jest.Mock).mockReturnValue({
      documents: mockDocuments,
      loading: false,
      error: null
    });
  });

  it('renders documents', async () => {
    render(<DocumentList />);

    await waitFor(() => {
      expect(screen.getByText('Document 1')).toBeInTheDocument();
      expect(screen.getByText('Document 2')).toBeInTheDocument();
    });
  });

  it('shows loading state', () => {
    (useDocuments as jest.Mock).mockReturnValue({
      documents: [],
      loading: true,
      error: null
    });

    render(<DocumentList />);
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('shows error state', () => {
    (useDocuments as jest.Mock).mockReturnValue({
      documents: [],
      loading: false,
      error: 'Failed to fetch documents'
    });

    render(<DocumentList />);
    expect(screen.getByText('Failed to fetch documents')).toBeInTheDocument();
  });
});
```

### 2. Integration Tests

```typescript
// src/__tests__/integration/DocumentFlow.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { store } from '../../store';
import { DocumentList } from '../../components/Document/DocumentList';
import { DocumentDetail } from '../../components/Document/DocumentDetail';

describe('Document Flow', () => {
  it('allows creating and viewing a document', async () => {
    render(
      <Provider store={store}>
        <DocumentList />
      </Provider>
    );

    // Create document
    fireEvent.click(screen.getByText('Create Document'));
    fireEvent.change(screen.getByLabelText('Title'), {
      target: { value: 'Test Document' }
    });
    fireEvent.click(screen.getByText('Save'));

    // Verify document appears in list
    await waitFor(() => {
      expect(screen.getByText('Test Document')).toBeInTheDocument();
    });

    // View document details
    fireEvent.click(screen.getByText('Test Document'));
    expect(screen.getByText('Document Details')).toBeInTheDocument();
  });
});
```

## Best Practices

1. **Component Design**:
   - Use functional components
   - Implement proper prop types
   - Follow single responsibility
   - Use composition over inheritance

2. **State Management**:
   - Use Redux for global state
   - Use local state for UI
   - Implement proper actions
   - Follow Redux patterns

3. **Routing**:
   - Implement route guards
   - Use lazy loading
   - Handle 404s
   - Maintain clean URLs

4. **API Integration**:
   - Use axios for requests
   - Implement interceptors
   - Handle errors properly
   - Use proper types

## Troubleshooting

1. **Component Issues**:
   - Check prop types
   - Verify component lifecycle
   - Check event handlers
   - Review state updates

2. **State Issues**:
   - Check Redux store
   - Verify action creators
   - Check reducers
   - Review selectors

3. **API Issues**:
   - Check network requests
   - Verify error handling
   - Check authentication
   - Review response types

## Additional Resources

- [React Documentation](https://reactjs.org/docs/getting-started.html)
- [Redux Documentation](https://redux.js.org/)
- [React Router Documentation](https://reactrouter.com/)
- [Material-UI Documentation](https://mui.com/)
