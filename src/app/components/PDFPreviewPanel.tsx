import { useEffect, useState } from 'react';
import { ExternalLink, FileText, Loader, XCircle } from 'lucide-react';

export function PDFPreviewPanel({ objectName }: { objectName?: string }) {
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);

  const proxyUrl = objectName
    ? `/__proxy/upload/proxy-file?objectName=${encodeURIComponent(objectName)}`
    : null;

  useEffect(() => {
    setLoading(Boolean(proxyUrl));
    setFailed(false);
    if (!proxyUrl) return;
    const timer = window.setTimeout(() => setLoading(false), 8000);
    return () => window.clearTimeout(timer);
  }, [proxyUrl]);

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-gray-800 flex items-center gap-2">
          <FileText size={15} className="text-red-500" /> PDF 预览
        </h2>
        {proxyUrl && (
          <a
            href={proxyUrl}
            target="_blank"
            rel="noreferrer"
            className="text-xs text-blue-600 hover:underline flex items-center gap-1"
          >
            <ExternalLink size={11} /> 新窗口打开
          </a>
        )}
      </div>
      <div className="w-full aspect-[210/297] rounded-lg overflow-hidden border border-gray-100 bg-gray-50 relative">
        {loading && !failed && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/70 text-gray-400 text-xs gap-2">
            <Loader size={14} className="animate-spin" /> 加载中...
          </div>
        )}
        {failed ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 text-xs gap-2">
            <XCircle size={32} className="text-red-300" />
            <p>预览加载失败</p>
            {proxyUrl && (
              <a href={proxyUrl} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
                点击下载查看
              </a>
            )}
          </div>
        ) : (
          proxyUrl && (
            <iframe
              key={proxyUrl}
              src={`${proxyUrl}#toolbar=1&navpanes=0&scrollbar=1`}
              className="w-full h-full"
              title="PDF Preview"
              onLoad={() => setLoading(false)}
              onError={() => { setLoading(false); setFailed(true); }}
            />
          )
        )}
      </div>
    </div>
  );
}
