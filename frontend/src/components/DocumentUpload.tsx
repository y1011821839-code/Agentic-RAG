import React from 'react';

interface Props {
  onUpload: (file: File) => void;
  uploading: boolean;
  documentCount: number;
  onClear: () => void;
}

export const DocumentUpload: React.FC<Props> = ({ onUpload, uploading, documentCount, onClear }) => {
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
      e.target.value = '';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="text-lg font-semibold mb-3 text-gray-800">📚 知识库管理</h3>

      <div className="mb-4">
        <label className="block w-full cursor-pointer">
          <div className={`border-2 border-dashed border-gray-300 rounded-lg p-6 text-center transition-colors
            ${uploading ? 'bg-gray-100' : 'hover:border-blue-500 hover:bg-blue-50'}`}>
            <input
              type="file"
              accept=".txt,.md"
              onChange={handleFileChange}
              disabled={uploading}
              className="hidden"
            />
            {uploading ? (
              <div className="text-gray-600">⏳ 上传中...</div>
            ) : (
              <>
                <div className="text-blue-600 mb-2">📤 点击上传文档</div>
                <div className="text-gray-500 text-sm">支持 .txt 和 .md 格式</div>
              </>
            )}
          </div>
        </label>
      </div>

      <div className="flex justify-between items-center text-sm text-gray-600">
        <span>当前文档数量：{documentCount} 个块</span>
        {documentCount > 0 && (
          <button
            onClick={onClear}
            className="text-red-600 hover:text-red-700 hover:underline"
          >
            清空知识库
          </button>
        )}
      </div>
    </div>
  );
};
