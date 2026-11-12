import { DragDropContext, Draggable, Droppable, type DropResult } from '@hello-pangea/dnd'
import { Plus } from 'lucide-react'
import type { BoardStage, Client } from '../types'
import { DealCard } from './DealCard'

export function KanbanBoard({ stages, clients, onOpen, onAdd, onDrop, moving }: {
  stages: BoardStage[]
  clients: Map<number, Client>
  onOpen: (id: number) => void
  onAdd: (stage: number) => void
  onDrop: (result: DropResult) => void
  moving: boolean
}) {
  return <DragDropContext onDragEnd={onDrop}>
    <div className="kanban-scroll">
      <div className="kanban">
        {stages.map(stage => <section className="kanban-column" key={stage.id} aria-label={stage.name}>
          <header className="stage-header">
            <span className="stage-dot" style={{ backgroundColor: stage.color }} />
            <h3>{stage.name}</h3><span className="stage-count">{stage.deals.length}</span>
            <button className="icon-button stage-add" type="button" onClick={() => onAdd(stage.id)}
              aria-label={`Создать сделку в стадии «${stage.name}»`}><Plus size={16} /></button>
          </header>
          <Droppable droppableId={String(stage.id)}>
            {(provided, snapshot) => <div className={`stage-list ${snapshot.isDraggingOver ? 'drop-over' : ''}`}
              ref={provided.innerRef} {...provided.droppableProps}>
              {stage.deals.map((deal, index) => {
                const client = clients.get(deal.client_id)
                return <Draggable key={deal.id} draggableId={String(deal.id)} index={index} isDragDisabled={moving}>
                  {(card, state) => <DealCard deal={deal} company={client?.company || client?.name || '—'}
                    onOpen={onOpen} provided={card} dragging={state.isDragging} />}
                </Draggable>
              })}
              {provided.placeholder}
              {stage.deals.length === 0 && !snapshot.isDraggingOver && <div className="empty-column">Нет сделок</div>}
            </div>}
          </Droppable>
        </section>)}
      </div>
    </div>
  </DragDropContext>
}
