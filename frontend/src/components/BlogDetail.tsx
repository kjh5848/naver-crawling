import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Calendar, 
  User, 
  Globe, 
  Download,
  FileText,
  Image as ImageIcon,
  Clock,
  ExternalLink,
  Copy,
  Check
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'react-hot-toast';

const API_BASE_URL = 'http://localhost:8000';

interface BlogPost {
  title: string;
  content: string;
  author: string;
  published_date?: string;
  original_url: string;
  scraped_at: string;
  images: string[];
  content_length: number;
}

interface JobResult {
  job_id: string;
  status: string;
  results: BlogPost[];
  created_at: string;
  completed_at?: string;
}

const BlogDetail: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [jobData, setJobData] = useState<JobResult | null>(null);
  const [selectedPost, setSelectedPost] = useState<BlogPost | null>(null);
  const [loading, setLoading] = useState(true);
  const [copiedUrl, setCopiedUrl] = useState(false);

  useEffect(() => {
    if (jobId) {
      fetchJobDetails(jobId);
    }
  }, [jobId]);

  useEffect(() => {
    if (jobData && jobData.results.length > 0) {
      setSelectedPost(jobData.results[0]);
    }
  }, [jobData]);

  const fetchJobDetails = async (id: string) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/job/${id}`);
      setJobData(response.data);
    } catch (error) {
      console.error('Failed to fetch job details:', error);
      toast.error('작업 상세 정보를 가져올 수 없습니다');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedUrl(true);
      toast.success('URL이 복사되었습니다');
      setTimeout(() => setCopiedUrl(false), 2000);
    } catch (error) {
      toast.error('복사에 실패했습니다');
    }
  };

  const downloadResults = async (format: string) => {
    if (!jobId) return;
    
    try {
      const response = await axios.get(`${API_BASE_URL}/download/${jobId}?format=${format}`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `scraping_results_${jobId}.${format}`;
      link.click();
      
      toast.success('파일 다운로드를 시작했습니다');
    } catch (error) {
      toast.error('파일 다운로드에 실패했습니다');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-600">작업 정보를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (!jobData || jobData.results.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <button
            onClick={() => navigate('/')}
            className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 mb-6"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>돌아가기</span>
          </button>
          
          <div className="bg-white rounded-xl shadow-sm border p-8 text-center">
            <FileText className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">작업을 찾을 수 없습니다</h2>
            <p className="text-gray-600">해당 작업이 존재하지 않거나 결과가 없습니다.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="sticky-header">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/')}
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                <span>돌아가기</span>
              </button>
              
              <div className="h-6 w-px bg-gray-300"></div>
              
              <div>
                <h1 className="text-lg font-semibold text-gray-900">스크래핑 결과</h1>
                <p className="text-sm text-gray-600">{jobData.results.length}개 포스트</p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => downloadResults('json')}
                className="btn-primary"
              >
                <FileText className="w-4 h-4 mr-2" />
                JSON
              </button>
              <button
                onClick={() => downloadResults('csv')}
                className="flex items-center space-x-2 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                <Download className="w-4 h-4" />
                <span>CSV</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          
          {/* 왼쪽: 포스트 목록 */}
          <div className="lg:col-span-1">
            <div className="card">
              <div className="card-header">
                <h3 className="font-semibold text-gray-900">포스트 목록</h3>
              </div>
              
              <div className="max-h-[600px] overflow-y-auto">
                {jobData.results.map((post, index) => (
                  <div
                    key={index}
                    onClick={() => setSelectedPost(post)}
                    className={`post-list-item p-4 border-b cursor-pointer ${
                      selectedPost === post ? 'active' : ''
                    }`}
                  >
                    <h4 className="font-medium text-sm text-gray-900 line-clamp-2 mb-2">
                      {post.title || '제목 없음'}
                    </h4>
                    <div className="meta-info mb-1">
                      <User className="w-3 h-3" />
                      <span>{post.author || '작성자 미상'}</span>
                    </div>
                    {post.published_date && (
                      <div className="meta-info">
                        <Calendar className="w-3 h-3" />
                        <span>{new Date(post.published_date).toLocaleDateString('ko-KR')}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 오른쪽: 선택된 포스트 상세 */}
          <div className="lg:col-span-3">
            {selectedPost && (
              <div className="card fade-in">
                {/* 포스트 헤더 */}
                <div className="card-header">
                  <h1 className="text-2xl font-bold text-gray-900 mb-4">
                    {selectedPost.title || '제목 없음'}
                  </h1>
                  
                  <div className="flex flex-wrap items-center gap-4 mb-4">
                    <div className="meta-info">
                      <User className="w-4 h-4" />
                      <span>{selectedPost.author || '작성자 미상'}</span>
                    </div>
                    
                    {selectedPost.published_date && (
                      <div className="meta-info">
                        <Calendar className="w-4 h-4" />
                        <span>{new Date(selectedPost.published_date).toLocaleDateString('ko-KR')}</span>
                      </div>
                    )}
                    
                    <div className="meta-info">
                      <Clock className="w-4 h-4" />
                      <span>스크래핑: {new Date(selectedPost.scraped_at).toLocaleString('ko-KR')}</span>
                    </div>
                    
                    <span className="tag tag-blue">
                      <FileText className="w-3 h-3 mr-1" />
                      {selectedPost.content_length.toLocaleString()}자
                    </span>
                    
                    {selectedPost.images.length > 0 && (
                      <span className="tag tag-green">
                        <ImageIcon className="w-3 h-3 mr-1" />
                        {selectedPost.images.length}개 이미지
                      </span>
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Globe className="w-4 h-4 text-gray-400" />
                    <a
                      href={selectedPost.original_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 hover:underline flex items-center space-x-1"
                    >
                      <span className="text-sm truncate max-w-md">{selectedPost.original_url}</span>
                      <ExternalLink className="w-3 h-3 flex-shrink-0" />
                    </a>
                    <button
                      onClick={() => copyToClipboard(selectedPost.original_url)}
                      className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                      title="URL 복사"
                    >
                      {copiedUrl ? (
                        <Check className="w-4 h-4 text-green-500" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>

                {/* 포스트 내용 */}
                <div className="card-body">
                  <div className="blog-detail-content">
                    <div 
                      className="text-gray-800 leading-relaxed whitespace-pre-wrap"
                      dangerouslySetInnerHTML={{ 
                        __html: selectedPost.content || '<p class="text-gray-500 italic">내용이 없습니다.</p>' 
                      }}
                    />
                  </div>
                  
                  {/* 이미지들 */}
                  {selectedPost.images.length > 0 && (
                    <div className="mt-8 pt-6 border-t">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <ImageIcon className="w-5 h-5 mr-2" />
                        첨부된 이미지 ({selectedPost.images.length}개)
                      </h3>
                      <div className="image-gallery">
                        {selectedPost.images.map((imageUrl, index) => (
                          <div key={index} className="image-gallery-item group">
                            <img
                              src={imageUrl}
                              alt={`이미지 ${index + 1}`}
                              loading="lazy"
                              onError={(e) => {
                                const target = e.target as HTMLImageElement;
                                target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjNmNGY2Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5YTNhZiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuydtOuPuOyngCDroZzrk5XtlaDsiJgg7JeG7J2MPC90ZXh0Pjwvc3ZnPg==';
                              }}
                            />
                            <div className="image-gallery-overlay">
                              <a
                                href={imageUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                원본 보기
                              </a>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BlogDetail;