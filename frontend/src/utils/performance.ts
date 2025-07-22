/**
 * 性能监控工具
 * 用于监控应用性能指标和用户体验
 */

interface PerformanceMetrics {
  // 页面加载性能
  pageLoadTime: number;
  domContentLoadedTime: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  
  // 用户交互性能
  firstInputDelay?: number;
  cumulativeLayoutShift: number;
  
  // 自定义业务指标
  apiResponseTime?: number;
  fileUploadTime?: number;
  taskProcessingTime?: number;
  
  // 系统信息
  userAgent: string;
  timestamp: number;
}

class PerformanceMonitor {
  private metrics: Partial<PerformanceMetrics> = {};
  private observers: PerformanceObserver[] = [];

  constructor() {
    this.initMetrics();
    this.setupObservers();
  }

  private initMetrics(): void {
    // 获取基础性能指标
    if (typeof window !== 'undefined' && 'performance' in window) {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const paint = performance.getEntriesByType('paint');
      
      if (navigation) {
        this.metrics.pageLoadTime = navigation.loadEventEnd - navigation.fetchStart;
        this.metrics.domContentLoadedTime = navigation.domContentLoadedEventEnd - navigation.fetchStart;
      }
      
      // First Contentful Paint
      const fcpEntry = paint.find(entry => entry.name === 'first-contentful-paint');
      if (fcpEntry) {
        this.metrics.firstContentfulPaint = fcpEntry.startTime;
      }
      
      this.metrics.userAgent = navigator.userAgent;
      this.metrics.timestamp = Date.now();
    }
  }

  private setupObservers(): void {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) {
      return;
    }

    try {
      // Largest Contentful Paint
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        this.metrics.largestContentfulPaint = lastEntry.startTime;
      });
      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
      this.observers.push(lcpObserver);

      // First Input Delay
      const fidObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach(entry => {
          if (entry.processingStart > entry.startTime) {
            this.metrics.firstInputDelay = entry.processingStart - entry.startTime;
          }
        });
      });
      fidObserver.observe({ entryTypes: ['first-input'] });
      this.observers.push(fidObserver);

      // Cumulative Layout Shift
      let clsScore = 0;
      const clsObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          if (!entry.hadRecentInput) {
            clsScore += entry.value;
            this.metrics.cumulativeLayoutShift = clsScore;
          }
        });
      });
      clsObserver.observe({ entryTypes: ['layout-shift'] });
      this.observers.push(clsObserver);
    } catch (error) {
      console.warn('Performance observers setup failed:', error);
    }
  }

  /**
   * 记录API响应时间
   */
  recordApiResponse(url: string, duration: number, success: boolean): void {
    const metric = {
      url,
      duration,
      success,
      timestamp: Date.now(),
    };
    
    this.metrics.apiResponseTime = duration;
    
    // 发送到分析服务（可选）
    this.sendMetric('api_response', metric);
  }

  /**
   * 记录文件上传性能
   */
  recordFileUpload(fileSize: number, duration: number, success: boolean): void {
    const metric = {
      fileSize,
      duration,
      success,
      uploadSpeed: fileSize / (duration / 1000), // bytes per second
      timestamp: Date.now(),
    };
    
    this.metrics.fileUploadTime = duration;
    
    this.sendMetric('file_upload', metric);
  }

  /**
   * 记录任务处理时间
   */
  recordTaskProcessing(taskType: string, duration: number, success: boolean): void {
    const metric = {
      taskType,
      duration,
      success,
      timestamp: Date.now(),
    };
    
    this.metrics.taskProcessingTime = duration;
    
    this.sendMetric('task_processing', metric);
  }

  /**
   * 记录用户交互性能
   */
  recordUserInteraction(action: string, duration: number): void {
    const metric = {
      action,
      duration,
      timestamp: Date.now(),
    };
    
    this.sendMetric('user_interaction', metric);
  }

  /**
   * 获取当前性能指标
   */
  getMetrics(): Partial<PerformanceMetrics> {
    return { ...this.metrics };
  }

  /**
   * 生成性能报告
   */
  generateReport(): string {
    const report = {
      timestamp: new Date().toISOString(),
      url: window.location.href,
      metrics: this.metrics,
      scores: this.calculateScores(),
    };
    
    return JSON.stringify(report, null, 2);
  }

  /**
   * 计算性能评分
   */
  private calculateScores(): Record<string, { score: number; grade: string; advice: string }> {
    const scores: Record<string, { score: number; grade: string; advice: string }> = {};
    
    // Page Load Time Score (0-100)
    if (this.metrics.pageLoadTime) {
      const loadTime = this.metrics.pageLoadTime;
      let score = 100;
      let grade = 'A';
      let advice = '页面加载速度优秀';
      
      if (loadTime > 5000) {
        score = 20;
        grade = 'F';
        advice = '页面加载过慢，建议优化资源加载';
      } else if (loadTime > 3000) {
        score = 60;
        grade = 'C';
        advice = '页面加载速度一般，可以进一步优化';
      } else if (loadTime > 2000) {
        score = 80;
        grade = 'B';
        advice = '页面加载速度良好';
      }
      
      scores.pageLoad = { score, grade, advice };
    }
    
    // First Contentful Paint Score
    if (this.metrics.firstContentfulPaint) {
      const fcp = this.metrics.firstContentfulPaint;
      let score = 100;
      let grade = 'A';
      let advice = 'FCP 表现优秀';
      
      if (fcp > 3000) {
        score = 20;
        grade = 'F';
        advice = 'FCP 过长，用户体验差';
      } else if (fcp > 1800) {
        score = 60;
        grade = 'C';
        advice = 'FCP 需要优化';
      } else if (fcp > 1000) {
        score = 80;
        grade = 'B';
        advice = 'FCP 表现良好';
      }
      
      scores.firstContentfulPaint = { score, grade, advice };
    }
    
    // Cumulative Layout Shift Score
    if (this.metrics.cumulativeLayoutShift !== undefined) {
      const cls = this.metrics.cumulativeLayoutShift;
      let score = 100;
      let grade = 'A';
      let advice = '页面布局稳定';
      
      if (cls > 0.25) {
        score = 20;
        grade = 'F';
        advice = '页面布局不稳定，影响用户体验';
      } else if (cls > 0.1) {
        score = 60;
        grade = 'C';
        advice = '页面布局稍有不稳定';
      }
      
      scores.cumulativeLayoutShift = { score, grade, advice };
    }
    
    return scores;
  }

  /**
   * 发送性能指标（可集成第三方分析服务）
   */
  private sendMetric(type: string, data: any): void {
    // 这里可以集成 Google Analytics, Sentry, 或其他性能监控服务
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Performance] ${type}:`, data);
    }
    
    // 示例：发送到分析服务
    // analytics.track('performance_metric', {
    //   type,
    //   ...data
    // });
  }

  /**
   * 清理观察者
   */
  dispose(): void {
    this.observers.forEach(observer => {
      try {
        observer.disconnect();
      } catch (error) {
        console.warn('Failed to disconnect observer:', error);
      }
    });
    this.observers = [];
  }
}

// 创建全局性能监控实例
let performanceMonitor: PerformanceMonitor | null = null;

export const getPerformanceMonitor = (): PerformanceMonitor => {
  if (!performanceMonitor) {
    performanceMonitor = new PerformanceMonitor();
  }
  return performanceMonitor;
};

// 便捷的性能记录函数
export const recordApiCall = (url: string, duration: number, success: boolean) => {
  getPerformanceMonitor().recordApiResponse(url, duration, success);
};

export const recordFileUpload = (fileSize: number, duration: number, success: boolean) => {
  getPerformanceMonitor().recordFileUpload(fileSize, duration, success);
};

export const recordTaskProcessing = (taskType: string, duration: number, success: boolean) => {
  getPerformanceMonitor().recordTaskProcessing(taskType, duration, success);
};

export const recordUserInteraction = (action: string, duration: number) => {
  getPerformanceMonitor().recordUserInteraction(action, duration);
};

// 性能计时器辅助函数
export const createTimer = () => {
  const startTime = performance.now();
  
  return {
    end: () => performance.now() - startTime,
    endAndRecord: (type: string, metadata?: any) => {
      const duration = performance.now() - startTime;
      getPerformanceMonitor().recordUserInteraction(type, duration);
      return duration;
    },
  };
};

// React Hook 用于性能监控
export const usePerformanceMonitor = () => {
  const monitor = getPerformanceMonitor();
  
  return {
    recordApiCall,
    recordFileUpload,
    recordTaskProcessing,
    recordUserInteraction,
    createTimer,
    getMetrics: () => monitor.getMetrics(),
    generateReport: () => monitor.generateReport(),
  };
};

export default PerformanceMonitor;