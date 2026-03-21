export type AnalysisPhase =
  | 'init'
  | 'crawling'
  | 'technical'
  | 'onpage'
  | 'semantic'
  | 'ux'
  | 'core_complete'
  | 'ai'
  | 'ai_stream'
  | 'warning'
  | 'error'
  | 'complete'

export interface StreamEvent {
  phase: AnalysisPhase
  progress?: number
  message?: string
  chunk?: string
  data?: any
  action_plan?: Array<Record<string, any>>
  analysis_id?: string
  cached?: boolean
}

export interface AnalysisPayload {
  analysis_id: string
  url: string
  created_at: string
  technical: any
  onpage: any
  semantic: any
  ux: any
  ai_analysis: string
  action_plan: Array<Record<string, any>>
  crawl_errors?: Array<Record<string, string>>
}
