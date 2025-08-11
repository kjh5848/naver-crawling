import React, { useState, useEffect } from 'react';
import { Toaster, toast } from 'react-hot-toast';
import { 
  Globe, 
  Download, 
  Play, 
  Pause, 
  Trash2, 
  FileText, 
  Image, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Loader2,
  BarChart3,
  Settings
} from 'lucide-react';
import axios from 'axios';
import './App.css';

// API Base URL
const API_BASE_URL = 'http://localhost:8001';

interface ScrapingJob {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  total_urls: number;
  completed_urls: number;
  failed_urls: number;
  results: any[];
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

interface Stats {
  total_posts: number;
  total_images: number;
  active_jobs: number;
  recent_posts: Array<{
    title: string;
    author: string;
    scraped_at: string;
  }>;
}

function App() {
  const [urls, setUrls] = useState('');
  const [downloadImages, setDownloadImages] = useState(true);
  const [outputFormat, setOutputFormat] = useState('json');
  const [maxConcurrent, setMaxConcurrent] = useState(3);
  const [jobs, setJobs] = useState<ScrapingJob[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 작업 목록 새로고침
  const fetchJobs = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/jobs`);
      setJobs(response.data);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    }
  };

  // 통계 정보 가져오기
  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  // 컴포넌트 마운트 시 초기 데이터 로드
  useEffect(() => {
    fetchJobs();
    fetchStats();
    
    // 2초마다 작업 상태 업데이트 (더 빠른 피드백)
    const interval = setInterval(() => {
      fetchJobs();
      fetchStats();
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  // 동기 스크래핑 (즉시 결과)
  const handleSyncScraping = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!urls.trim()) {
      toast.error('URL을 입력해주세요');
      return;
    }

    setIsSubmitting(true);
    const toastId = toast.loading('스크래핑 중... 잠시만 기다려주세요');
    
    try {
      const urlList = urls.split('\n').filter(url => url.trim());
      
      const response = await axios.post(`${API_BASE_URL}/test-scrape`, {
        url: urlList[0] // 첫 번째 URL만 테스트
      }, {
        timeout: 120000 // 2분 타임아웃
      });

      if (response.data.success) {
        toast.success('스크래핑이 완료되었습니다!', { id: toastId });
        console.log('Scraping result:', response.data);
        // 결과를 화면에 표시하거나 저장
      } else {
        toast.error(`스크래핑 실패: ${response.data.error}`, { id: toastId });
      }
      
      setUrls(''); // 입력 필드 초기화
      
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '스크래핑에 실패했습니다', { id: toastId });
    } finally {
      setIsSubmitting(false);
    }
  };

  // 스크래핑 시작 (백그라운드)
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!urls.trim()) {
      toast.error('URL을 입력해주세요');
      return;
    }

    setIsSubmitting(true);
    
    try {
      const urlList = urls.split('\n').filter(url => url.trim());
      
      const response = await axios.post(`${API_BASE_URL}/scrape`, {
        urls: urlList,
        download_images: downloadImages,
        output_format: outputFormat,
        max_concurrent: maxConcurrent,
        headless: true
      });

      toast.success(response.data.message);
      setUrls(''); // 입력 필드 초기화
      fetchJobs(); // 작업 목록 새로고침
      
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '스크래핑 시작에 실패했습니다');
    } finally {
      setIsSubmitting(false);
    }
  };

  // 작업 삭제
  const deleteJob = async (jobId: string) => {
    try {
      await axios.delete(`${API_BASE_URL}/job/${jobId}`);
      toast.success('작업이 삭제되었습니다');
      fetchJobs();
    } catch (error) {
      toast.error('작업 삭제에 실패했습니다');
    }
  };

  // 결과 다운로드
  const downloadResults = async (jobId: string, format: string) => {
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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'running': return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed': return <XCircle className="w-4 h-4 text-red-500" />;
      default: return null;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending': return '대기 중';
      case 'running': return '실행 중';
      case 'completed': return '완료';
      case 'failed': return '실패';
      default: return status;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Toaster position="top-right" />
      
      {/* 헤더 */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center space-x-3">
            <Globe className="w-8 h-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">네이버 블로그 스크래퍼</h1>
          </div>
          <p className="mt-2 text-gray-600">네이버 블로그 컨텐츠를 쉽게 추출하고 관리하세요</p>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* 왼쪽: 스크래핑 폼 */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-xl font-semibold mb-6 flex items-center">
                <Settings className="w-5 h-5 mr-2 text-gray-600" />
                스크래핑 설정
              </h2>
              
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* URL 입력 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    네이버 블로그 URL (한 줄에 하나씩)
                  </label>
                  <textarea
                    value={urls}
                    onChange={(e) => setUrls(e.target.value)}
                    placeholder="https://blog.naver.com/example/123456789"
                    rows={6}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                    required
                  />
                </div>

                {/* 옵션들 */}
                <div className="space-y-4">
                  {/* 이미지 다운로드 */}
                  <label className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={downloadImages}
                      onChange={(e) => setDownloadImages(e.target.checked)}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">이미지도 함께 다운로드</span>
                  </label>

                  {/* 출력 형식 */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      출력 형식
                    </label>
                    <select
                      value={outputFormat}
                      onChange={(e) => setOutputFormat(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="json">JSON</option>
                      <option value="csv">CSV</option>
                      <option value="markdown">Markdown</option>
                    </select>
                  </div>

                  {/* 동시 실행 수 */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      동시 실행 수: {maxConcurrent}
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={maxConcurrent}
                      onChange={(e) => setMaxConcurrent(Number(e.target.value))}
                      className="w-full"
                    />
                  </div>
                </div>

                {/* 실행 버튼들 */}
                <div className="space-y-3">
                  {/* 즉시 결과 버튼 */}
                  <button
                    type="button"
                    onClick={handleSyncScraping}
                    disabled={isSubmitting}
                    className="w-full bg-green-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-green-700 focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span>스크래핑 중...</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle className="w-5 h-5" />
                        <span>즉시 결과 보기 (테스트)</span>
                      </>
                    )}
                  </button>

                  {/* 백그라운드 처리 버튼 */}
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span>시작 중...</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-5 h-5" />
                        <span>백그라운드 처리</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>

            {/* 통계 카드 */}
            {stats && (
              <div className="mt-6 bg-white rounded-xl shadow-sm border p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <BarChart3 className="w-5 h-5 mr-2 text-gray-600" />
                  통계
                </h3>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{stats.total_posts}</div>
                    <div className="text-sm text-gray-600">총 포스트</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{stats.total_images}</div>
                    <div className="text-sm text-gray-600">총 이미지</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">{stats.active_jobs}</div>
                    <div className="text-sm text-gray-600">진행 중</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">{jobs.length}</div>
                    <div className="text-sm text-gray-600">전체 작업</div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* 오른쪽: 작업 목록 */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm border">
              <div className="p-6 border-b">
                <h2 className="text-xl font-semibold">스크래핑 작업</h2>
              </div>
              
              <div className="p-6">
                {jobs.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <Globe className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>아직 스크래핑 작업이 없습니다.</p>
                    <p className="text-sm">왼쪽에서 URL을 입력하고 시작해보세요!</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {jobs.map((job) => (
                      <div key={job.job_id} className="border rounded-lg p-4 hover:bg-gray-50">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center space-x-3">
                            {getStatusIcon(job.status)}
                            <span className="font-medium">{getStatusText(job.status)}</span>
                            <span className="text-sm text-gray-500">
                              {new Date(job.created_at).toLocaleString('ko-KR')}
                            </span>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            {job.status === 'completed' && (
                              <>
                                <button
                                  onClick={() => downloadResults(job.job_id, 'json')}
                                  className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                                  title="JSON 다운로드"
                                >
                                  <FileText className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => downloadResults(job.job_id, 'csv')}
                                  className="p-2 text-green-600 hover:bg-green-50 rounded-lg"
                                  title="CSV 다운로드"
                                >
                                  <Download className="w-4 h-4" />
                                </button>
                              </>
                            )}
                            <button
                              onClick={() => deleteJob(job.job_id)}
                              className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                              title="작업 삭제"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>

                        {/* 진행률 바 */}
                        {job.status === 'running' && (
                          <div className="mb-3">
                            <div className="flex justify-between text-sm text-gray-600 mb-1">
                              <span>진행률</span>
                              <span>{job.progress}%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${job.progress}%` }}
                              ></div>
                            </div>
                          </div>
                        )}

                        {/* 작업 정보 */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-gray-600">총 URL:</span>
                            <span className="ml-1 font-medium">{job.total_urls}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">완료:</span>
                            <span className="ml-1 font-medium text-green-600">{job.completed_urls}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">실패:</span>
                            <span className="ml-1 font-medium text-red-600">{job.failed_urls}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">결과:</span>
                            <span className="ml-1 font-medium">{job.results.length}</span>
                          </div>
                        </div>

                        {/* 에러 메시지 */}
                        {job.error_message && (
                          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                            <p className="text-sm text-red-600">{job.error_message}</p>
                          </div>
                        )}

                        {/* 완료된 작업의 결과 미리보기 */}
                        {job.status === 'completed' && job.results.length > 0 && (
                          <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                            <p className="text-sm text-green-600 font-medium">
                              ✅ {job.results.length}개 포스트 스크래핑 완료
                            </p>
                            <div className="mt-2 text-xs text-green-600">
                              최근 포스트: {job.results[0]?.title || '제목 없음'}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;