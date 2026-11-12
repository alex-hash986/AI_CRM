export type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue }

export interface Entity {
  id: number
  created_at: string
  updated_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

export interface Client extends Entity {
  name: string
  company: string | null
  email: string | null
  phone: string | null
  status: string
  custom_fields: Record<string, JsonValue>
}

export interface ClientDetail extends Client {
  deals: DealShort[]
}

export interface DealShort {
  id: number
  title: string
  budget: string
  currency: string
  stage_id: number
  client_id: number
  ai_score: number | null
  ai_win_probability: number | null
}

export interface Deal extends DealShort, Entity {
  ai_next_step: string | null
  ai_risk_assessment: string | null
  closed_at: string | null
}

export interface DealCreate {
  title: string
  budget: string
  currency: string
  stage_id: number
  client_id: number
}

export interface PipelineStage {
  id: number
  name: string
  order: number
  color: string
  is_won: boolean
  is_lost: boolean
}

export interface BoardStage extends PipelineStage {
  deals: DealShort[]
}

export interface Board {
  pipeline_id: number
  stages: BoardStage[]
}

export interface StageMetrics {
  stage_id: number
  stage_name: string
  deal_count: number
  total_amount: string
  weighted_amount: string
}

export interface SalesDashboard {
  currency: string | null
  total_pipeline_value: string
  weighted_forecast_value: string
  won_deals_revenue: string
  average_ai_score: number | null
  conversion_rate: number
  stages_breakdown: StageMetrics[]
}

export interface DealScoringOutput {
  score: number
  win_probability: number
  risk_assessment: string
  next_step: string
}

export type EmailTemplate = 'follow_up' | 'cold_outreach' | 'proposal_pitch' | 'reengagement'
export type EmailTone = 'friendly' | 'formal' | 'direct'

export interface EmailGenerateRequest {
  deal_id: number
  template_type: EmailTemplate
  tone: EmailTone
  custom_instructions?: string | null
}

export interface EmailDraft {
  subject: string
  body: string
  key_points: string[]
}

export interface TaskStatus<T> {
  task_id: string
  status: string
  result: T | { error: string } | null
}

export type Channel = 'email' | 'telegram' | 'call' | 'note'
export type Direction = 'inbound' | 'outbound'

export interface CommunicationCreate {
  deal_id?: number | null
  client_id: number
  channel: Channel
  direction: Direction
  content: string
}

export interface Communication extends Entity {
  deal_id: number | null
  client_id: number
  channel: Channel
  direction: Direction
  content: string
  ai_summary: string | null
}

export interface CommunicationCreated extends Communication {
  task_id: string | null
}

export interface EmailSendRequest {
  deal_id: number
  to_email: string
  subject: string
  body: string
}

export interface EmailSendResponse {
  status: 'sent'
  delivery_mode: 'smtp' | 'demo'
  communication: Communication
}

export interface TelegramRequest {
  chat_id: string
  username?: string
  text: string
}

export interface TelegramResponse {
  status: 'accepted' | 'duplicate' | 'ignored'
  communication_id: number | null
  task_id: string | null
  deal_id: number | null
}
