import React, { useState, useEffect } from 'react';
import FileUploader from '../components/FileUploader';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const UploadPage = () => {
  const [notification, setNotification] = useState(null);
  const [existingSources, setExistingSources] = useState([]);
  const [isLoadingSources, setIsLoadingSources] = useState(true);
  const [stats, setStats] = useState(null);
  const [deleteConfirmation, setDeleteConfirmation] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const showNotification = (message, type = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 5000);
  };

  const fetchExistingSources = async () => {
    try {
      setIsLoadingSources(true);
      const response = await axios.get(`${API_BASE_URL}/debug/stats`);
      setStats(response.data);
      
      // Get unique sources from the uploads directory
      try {
        const uploadsResponse = await axios.get(`${API_BASE_URL}/uploads`);
        setExistingSources(uploadsResponse.data.files || []);
      } catch (error) {
        console.log('Uploads endpoint not available, showing basic stats');
      }
      
    } catch (error) {
      console.error('Error fetching sources:', error);
      showNotification('Failed to load existing sources', 'error');
    } finally {
      setIsLoadingSources(false);
    }
  };

  useEffect(() => {
    fetchExistingSources();
  }, []);

  const handleUpload = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      showNotification(`Successfully uploaded: ${file.name}`, 'success');
      // Refresh sources after upload
      fetchExistingSources();
      return response.data;
    } catch (error) {
      console.error('Upload error:', error);
      showNotification(`Failed to upload: ${file.name}`, 'error');
      throw error;
    }
  };

  const handleIngest = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/ingest`);
      showNotification(`Successfully processed ${response.data.files?.length || 0} documents`, 'success');
      // Refresh sources after ingestion
      fetchExistingSources();
      return response.data;
    } catch (error) {
      console.error('Ingest error:', error);
      showNotification('Failed to process documents', 'error');
      throw error;
    }
  };

  const handleDeleteClick = (filename) => {
    setDeleteConfirmation({
      filename,
      message: `Are you sure you want to delete "${filename}"? This will remove the document and all its associated embeddings from the knowledge base.`
    });
  };

  const handleDeleteConfirm = async () => {
    if (!deleteConfirmation) return;
    
    setIsDeleting(true);
    try {
      const response = await axios.delete(`${API_BASE_URL}/documents/${encodeURIComponent(deleteConfirmation.filename)}`);
      showNotification(response.data.message, 'success');
      
      // Refresh sources after deletion
      await fetchExistingSources();
      
    } catch (error) {
      console.error('Delete error:', error);
      showNotification(`Failed to delete: ${deleteConfirmation.filename}`, 'error');
    } finally {
      setIsDeleting(false);
      setDeleteConfirmation(null);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteConfirmation(null);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Document Sources</h1>
        <p className="text-gray-600">
          Manage your document collection for the chatbot knowledge base.
        </p>
      </div>

      {notification && (
        <div className={`mb-6 p-4 rounded-lg ${
          notification.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' :
          notification.type === 'error' ? 'bg-red-50 text-red-800 border border-red-200' :
          'bg-blue-50 text-blue-800 border border-blue-200'
        }`}>
          {notification.message}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirmation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Confirm Deletion</h3>
            <p className="text-gray-600 mb-6">{deleteConfirmation.message}</p>
            <div className="flex space-x-3 justify-end">
              <button
                onClick={handleDeleteCancel}
                disabled={isDeleting}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteConfirm}
                disabled={isDeleting}
                className="px-4 py-2 text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50 flex items-center"
              >
                {isDeleting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Deleting...
                  </>
                ) : (
                  'Delete'
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Existing Sources */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Current Knowledge Base</h2>
          
          {isLoadingSources ? (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-sm text-gray-600 mt-2">Loading sources...</p>
            </div>
          ) : (
            <div className="space-y-4">
              {stats && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">Total Chunks:</span>
                      <span className="ml-2 text-gray-900">{stats.document_count}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">LLM Model:</span>
                      <span className="ml-2 text-gray-900">{stats.llm_model}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Chunk Size:</span>
                      <span className="ml-2 text-gray-900">{stats.chunk_size}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Ollama Status:</span>
                      <span className={`ml-2 ${stats.ollama_available ? 'text-green-600' : 'text-red-600'}`}>
                        {stats.ollama_available ? '✓ Connected' : '✗ Disconnected'}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {existingSources.length > 0 ? (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Uploaded Documents:</h3>
                  <div className="space-y-2">
                    {existingSources.map((source, index) => (
                      <div key={index} className="flex items-center text-sm text-gray-600 bg-gray-50 rounded p-2">
                        <span className="text-green-500 mr-2">📄</span>
                        <div className="flex-1">
                          <div className="font-medium">{source.name}</div>
                          <div className="text-xs text-gray-400">
                            {Math.round(source.size / 1024)} KB
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs text-gray-400">Active</span>
                          <button
                            onClick={() => handleDeleteClick(source.name)}
                            className="text-red-500 hover:text-red-700 p-1 rounded transition-colors"
                            title="Delete document"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-2">📚</div>
                  <p className="text-sm">No documents uploaded yet</p>
                  <p className="text-xs">Upload PDFs to start building your knowledge base</p>
                </div>
              )}

              <button
                onClick={fetchExistingSources}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                🔄 Refresh Sources
              </button>
            </div>
          )}
        </div>

        {/* Upload New Documents */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Add New Documents</h2>
          <FileUploader onUpload={handleUpload} onIngest={handleIngest} />
        </div>
      </div>
    </div>
  );
};

export default UploadPage; 