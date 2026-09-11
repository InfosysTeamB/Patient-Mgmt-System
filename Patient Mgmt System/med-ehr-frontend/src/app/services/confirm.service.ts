import { Injectable } from '@angular/core';

export interface ConfirmOptions {
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  danger?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class ConfirmService {
  private opts: ConfirmOptions | null = null;
  private resolver: ((result: boolean) => void) | null = null;

  confirm(options: ConfirmOptions): Promise<boolean> {
    this.opts = {
      confirmText: 'Confirm',
      cancelText: 'Cancel',
      danger: false,
      ...options
    };
    return new Promise(resolve => {
      this.resolver = resolve;
    });
  }

  getOptions(): ConfirmOptions | null {
    return this.opts;
  }

  isOpen(): boolean {
    return this.opts !== null;
  }

  accept(): void {
    if (this.resolver) {
      this.resolver(true);
      this.resolver = null;
      this.opts = null;
    }
  }

  reject(): void {
    if (this.resolver) {
      this.resolver(false);
      this.resolver = null;
      this.opts = null;
    }
  }
}