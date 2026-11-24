import { render, screen } from '@testing-library/react';
import BerandaPage from './pages/BerandaPage';

test('renders Bvision home page', () => {
  render(<BerandaPage />);

  expect(
    screen.getByRole('heading', {
      name: /pelajari bahasa isyarat lebih menyenangkan/i,
    })
  ).toBeInTheDocument();
});
