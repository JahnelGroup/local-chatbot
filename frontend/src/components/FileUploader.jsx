import React, { useState, useCallback } from 'react';
import LoadingSpinner from './LoadingSpinner';

const FileUploader = ({ onUpload, onIngest }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files).filter(
      file => file.type === 'application/pdf'
    );
    
    if (files.length > 0) {
      handleUpload(files);
    }
  }, []);

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files).filter(
      file => file.type === 'application/pdf'
    );
    
    if (files.length > 0) {
      handleUpload(files);
    }
  };

  const handleUpload = async (files) => {
    setIsUploading(true);
    
    for (const file of files) {
      try {
        await onUpload(file);
        setUploadedFiles(prev => [...prev, file.name]);
      } catch (error) {
        console.error('Upload failed:', error);
      }
    }
    
    setIsUploading(false);
  };

  const handleIngest = async () => {
    setIsIngesting(true);
    try {
      await onIngest();
    } catch (error) {
      console.error('Ingestion failed:', error);
    }
    setIsIngesting(false);
  };

  return (
    <div className="space-y-4">
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="space-y-2">
          <div className="text-4xl">📄</div>
          <div className="text-lg font-medium text-gray-900">
            Upload PDF Documents
          </div>
          <div className="text-sm text-gray-600">
            Drag and drop PDF files here, or click to select
          </div>
          <input
            type="file"
            accept=".pdf"
            multiple
            onChange={handleFileSelect}
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer transition-colors"
          >
            Select Files
          </label>
        </div>
      </div>

      {isUploading && (
        <div className="text-center">
          <LoadingSpinner text="Uploading files..." />
        </div>
      )}

      {uploadedFiles.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-medium text-gray-900">Uploaded Files:</h3>
          <div className="space-y-1">
            {uploadedFiles.map((filename, index) => (
              <div key={index} className="text-sm text-gray-600 flex items-center">
                <span className="text-green-500 mr-2">✓</span>
                {filename}
              </div>
            ))}
          </div>
          <button
            onClick={handleIngest}
            disabled={isIngesting}
            className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isIngesting ? <LoadingSpinner size="sm" text="Processing documents..." /> : 'Process Documents'}
          </button>
        </div>
      )}
    </div>
  );
};

export default FileUploader; 