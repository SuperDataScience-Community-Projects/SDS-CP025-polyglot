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

  audioContext: AudioContext | null = null;

  @ViewChild('messagesEnd') private readonly messagesEnd!: ElementRef;
  private readonly http: HttpClient =  inject(HttpClient);
  awaitingResponse = signal<boolean>(false);

  constructor() {
    this.audioContext = new (window.AudioContext)();
  }


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
    this.awaitingResponse.set(true);
    this.http.post<{role: string, message: string, voice?: any}>(`${this.baseUrl}/chat`, {input }, {withCredentials: true}).subscribe({
      next: (response) => {
        this.history().push(response);
        if (response.voice) {
          this.decodeAndPlayAudio(this.base64ToArrayBuffer(response.voice))
        }
        setTimeout(() => this.scrollToBottom(), 100);
      },
      complete: () => this.awaitingResponse.set(false)
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

  decodeAndPlayAudio(data: ArrayBuffer) {
    if (this.audioContext) {
      this.audioContext.decodeAudioData(data, (buffer) => {
        // Create a buffer source node
        const source = this.audioContext!.createBufferSource();
        source.buffer = buffer;

        // Connect the source node to the audio context's destination (the speakers)
        source.connect(this.audioContext!.destination);

        // Start the audio
        source.start();

        // Optional: Handle the end of the audio
        source.onended = () => {
          console.log('Audio playback finished');
        };
      }, (error) => {
        console.error('Error decoding audio data', error);
      });
    }
  }

  base64ToArrayBuffer(base64: string): ArrayBuffer {
    const binaryString = window.atob(base64);  // Decode base64 string to binary string
    const len = binaryString.length;
    const buffer = new ArrayBuffer(len);
    const view = new Uint8Array(buffer);

    for (let i = 0; i < len; i++) {
      view[i] = binaryString.charCodeAt(i);
    }
    return buffer;
  }
}
