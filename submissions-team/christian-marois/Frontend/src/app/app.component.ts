import {AfterViewChecked, AfterViewInit, Component, ElementRef, inject, signal, ViewChild} from '@angular/core';
import { initFlowbite } from 'flowbite';
import {HttpClient} from '@angular/common/http';
import {CommonModule} from '@angular/common';

@Component({
  selector: 'app-root',
  imports: [CommonModule],
  templateUrl: './app.component.html'
})
export class AppComponent implements AfterViewInit, AfterViewChecked {
  baseUrl = 'http://localhost:3000'
  title = 'Language Tutor';
  history = signal<any[]>([])
  userMessage = signal<string>('');

  @ViewChild('messagesEnd') private messagesEnd!: ElementRef;
  private readonly http: HttpClient =  inject(HttpClient);

  ngAfterViewInit(): void {
    initFlowbite();
    this.getHistory();
  }

  ngAfterViewChecked() {
    this.scrollToBottom();
  }

  private scrollToBottom(): void {
    this.messagesEnd?.nativeElement?.scrollIntoView({ behavior: 'smooth' });
  }

  chat(input: string){
    this.http.post(`${this.baseUrl}/chat`, {input }, {withCredentials: true}).subscribe((response) => {
      this.history().push( response);
      setTimeout(() => this.scrollToBottom(), 100);
    })

  }

  getHistory(){
    this.http.get(`${this.baseUrl}/history`, {withCredentials: true}).subscribe((response: any) => {
      this.history.set(response);
      setTimeout(() => this.scrollToBottom(), 100);
    })
  }

  startTutoring() {
    this.chat('init')
  }

  sendMessage($event?: KeyboardEvent) {
    if( this.userMessage() && (!$event || $event.code === 'Enter') ) {
      this.history().push( {role: 'Human', message: this.userMessage()})
      this.chat(this.userMessage());
      this.userMessage.set('')
      setTimeout(() => this.scrollToBottom(), 100);
    }
  }

  protected readonly HTMLTextAreaElement = HTMLTextAreaElement;
}
