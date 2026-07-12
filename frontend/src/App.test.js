import { render, screen } from '@testing-library/react';
import App from './App';
import { LanguageProvider } from './language/LanguageContext';

jest.mock('react-plotly.js', () => () => <div data-testid="plot" />);

test('renders the authentication screen when signed out', () => {
  localStorage.clear();
  render(
    <LanguageProvider>
      <App />
    </LanguageProvider>
  );
  expect(screen.getByRole('heading', { name: /welcome back/i })).toBeInTheDocument();
});
