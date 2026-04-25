import { Component, ElementRef, ViewChild, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { JsonPipe } from '@angular/common';

interface ChatEvent {
  id: number;
  kind: 'user' | 'tool_start' | 'tool_end' | 'agent_thinking' | 'interrupt' | 'done' | 'error';
  text?: string;
  tool?: string;
  toolInput?: unknown;
  toolOutput?: string;
  checkpoints?: Array<{ tool_results: Array<{ tool: string; content: string }> }>;
}

@Component({
    selector: 'app-root',
    imports: [FormsModule, JsonPipe],
    templateUrl: './app.component.html',
    styleUrl: './app.component.css'
})
export class AppComponent {
  @ViewChild('chatEnd') chatEnd!: ElementRef;

  // Plain properties for ngModel two-way binding
  query = '';
  userId = '';

  // Signals drive the reactive display
  events = signal<ChatEvent[]>([]);
  isStreaming = signal(false);
  isInterrupted = signal(false);
  currentTokens = signal('');
  currentThreadId = signal<string | null>(null);

  private nextId = 0;
  private readonly API = 'http://localhost:8000';

  private id() {
    return this.nextId++;
  }

  private push(ev: Omit<ChatEvent, 'id'>) {
    this.events.update(list => [...list, { id: this.id(), ...ev }]);
    setTimeout(() => this.chatEnd?.nativeElement?.scrollIntoView({ behavior: 'smooth' }), 30);
  }

  private flushTokens() {
    const t = this.currentTokens().trim();
    if (t) {
      this.push({ kind: 'agent_thinking', text: this.currentTokens() });
      this.currentTokens.set('');
    }
  }

  async submit() {
    const q = this.query.trim();
    if (!q || this.isStreaming()) return;

    this.events.set([]);
    this.currentTokens.set('');
    this.currentThreadId.set(null);
    this.isInterrupted.set(false);
    this.isStreaming.set(true);
    this.push({ kind: 'user', text: q });
    this.query = '';

    try {
      await this.streamAgent(q, this.userId || undefined);
    } finally {
      this.isStreaming.set(false);
    }
  }

  async validate(approved: boolean) {
    const tid = this.currentThreadId();
    if (!tid) return;
    this.isInterrupted.set(false);
    await fetch(`${this.API}/agent/${tid}/resume`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approved }),
    });
  }

  private async streamAgent(query: string, userId?: string) {
    const resp = await fetch(`${this.API}/agent/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, user_id: userId ?? null }),
    });

    if (!resp.body) return;
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const parts = buffer.split('\n\n');
      buffer = parts.pop() ?? '';
      for (const part of parts) {
        if (part.trim()) this.handleBlock(part);
      }
    }
  }

  private handleBlock(block: string) {
    let eventType = '';
    let dataStr = '';
    for (const line of block.split('\n')) {
      if (line.startsWith('event: ')) eventType = line.slice(7).trim();
      if (line.startsWith('data: ')) dataStr = line.slice(6);
    }
    if (!dataStr) return;

    let data: Record<string, unknown>;
    try {
      data = JSON.parse(dataStr);
    } catch {
      return;
    }

    switch (eventType) {
      case 'start':
        this.currentThreadId.set(data['thread_id'] as string);
        break;

      case 'token':
        this.currentTokens.update(t => t + ((data['content'] as string) ?? ''));
        setTimeout(() => this.chatEnd?.nativeElement?.scrollIntoView({ behavior: 'smooth' }), 10);
        break;

      case 'tool_start':
        this.flushTokens();
        this.push({ kind: 'tool_start', tool: data['tool'] as string, toolInput: data['input'] });
        break;

      case 'tool_end':
        this.push({ kind: 'tool_end', tool: data['tool'] as string, toolOutput: data['output'] as string });
        break;

      case 'interrupt':
        this.flushTokens();
        this.currentThreadId.set(data['thread_id'] as string);
        this.push({
          kind: 'interrupt',
          checkpoints: data['checkpoints'] as ChatEvent['checkpoints'],
        });
        this.isInterrupted.set(true);
        break;

      case 'done':
        this.flushTokens();
        this.push({ kind: 'done' });
        break;

      case 'error':
        this.flushTokens();
        this.push({ kind: 'error', text: data['message'] as string });
        break;
    }
  }
}
