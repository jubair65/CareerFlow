import {
  Component,
  type ComponentType,
  type ErrorInfo,
  type ReactNode,
} from 'react';

export interface ErrorFallbackProps {
  error: Error;
  resetError: () => void;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  FallbackComponent?: ComponentType<ErrorFallbackProps>;
  /** Changing this clears a caught error. Pass the route to recover on navigation. */
  resetKey?: unknown;
}

interface ErrorBoundaryState {
  error: Error | null;
}

function toError(value: unknown): Error {
  if (value instanceof Error) {
    return value;
  }
  if (typeof value === 'string') {
    return new Error(value);
  }
  try {
    return new Error(JSON.stringify(value));
  } catch {
    return new Error(String(value));
  }
}

function DefaultFallback({ error, resetError }: ErrorFallbackProps) {
  const isExtraction =
    error?.message?.toLowerCase().includes('extract') ||
    error?.message?.toLowerCase().includes('document') ||
    error?.message?.toLowerCase().includes('cv');

  return (
    <div
      className="min-h-screen w-full flex items-center justify-center bg-gray-50 p-6"
      data-testid="error-boundary-fallback"
    >
      <div className="max-w-lg w-full text-center rounded-2xl bg-white p-8 shadow-sm border border-gray-200">
        <h1 className="text-xl font-bold text-gray-900" data-testid="error-boundary-title">
          {isExtraction ? 'Unable to extract text from document' : 'Something went wrong'}
        </h1>
        <p className="mt-2 text-sm text-gray-600" data-testid="error-boundary-advice">
          {isExtraction
            ? 'Ensure document is not password-protected or scanned as raw image.'
            : 'This part of the app hit an error. The rest of the app is still running.'}
        </p>
        {import.meta.env.DEV ? (
          <pre className="mt-4 overflow-x-auto rounded bg-gray-100 p-3 text-left text-xs text-gray-800">
            {error.message || String(error)}
          </pre>
        ) : null}
        <div className="mt-6 flex items-center justify-center gap-3">
          <button
            type="button"
            onClick={resetError}
            data-testid="button-retry-extraction"
            className="rounded-xl bg-[#253142] px-4 py-2.5 text-xs font-bold text-white hover:bg-gray-700 transition"
          >
            Retry extraction
          </button>
          <a
            href="/student/cv"
            data-testid="button-try-another-file"
            className="rounded-xl border border-gray-300 bg-white px-4 py-2.5 text-xs font-bold text-gray-700 hover:bg-gray-50 transition"
          >
            Try another file
          </a>
        </div>
      </div>
    </div>
  );
}

export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: unknown): ErrorBoundaryState {
    return { error: toError(error) };
  }

  componentDidCatch(error: unknown, info: ErrorInfo): void {
    console.error(
      'ErrorBoundary caught an error:',
      toError(error),
      info.componentStack,
    );
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps): void {
    if (
      this.state.error !== null &&
      prevProps.resetKey !== this.props.resetKey
    ) {
      this.resetError();
    }
  }

  resetError = (): void => {
    this.setState({ error: null });
  };

  render(): ReactNode {
    const { error } = this.state;
    if (error === null) {
      return this.props.children;
    }
    const Fallback = this.props.FallbackComponent ?? DefaultFallback;
    return <Fallback error={error} resetError={this.resetError} />;
  }
}
