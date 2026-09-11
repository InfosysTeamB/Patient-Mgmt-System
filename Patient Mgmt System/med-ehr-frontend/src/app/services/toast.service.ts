import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface Toast {
  id: number;
  type: 'success' | 'error' | 'info';
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class ToastService {
  private toastsSubject = new BehaviorSubject<Toast[]>([]);
  toasts$ = this.toastsSubject.asObservable();
  private counter = 0;

  show(type: 'success' | 'error' | 'info', message: string): void {
    const id = ++this.counter;
    const toasts = this.toastsSubject.getValue();
    this.toastsSubject.next([...toasts, { id, type, message }]);
    window.setTimeout(() => this.dismiss(id), 3500);
  }

  success(message: string): void {
    this.show('success', message);
  }

  error(message: string): void {
    this.show('error', message);
  }

  info(message: string): void {
    this.show('info', message);
  }

  dismiss(id: number): void {
    const toasts = this.toastsSubject.getValue();
    this.toastsSubject.next(toasts.filter(t => t.id !== id));
  }
}