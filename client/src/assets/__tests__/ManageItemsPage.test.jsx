import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import ManageItemsPage from '../ManageItemsPage';
import axios from 'axios';

jest.mock('axios');

describe('ManageItemsPage', () => {
  afterEach(() => jest.resetAllMocks());

  test('renders string list and deletes item', async () => {
    axios.get.mockResolvedValueOnce({ data: ['legs', 'chest'] });
    axios.delete.mockResolvedValueOnce({ data: { message: 'Deleted' } });

    render(<ManageItemsPage title="Body Parts" fetchUrl="/api/v1/body_parts_list" deleteUrl="/api/v1/delete_body_part" />);

    await waitFor(() => expect(screen.getByText('legs')).toBeInTheDocument());

    // Click delete on 'legs'
    const deleteButtons = screen.getAllByText('Delete');
    fireEvent.click(deleteButtons[0]);

    // Confirm dialog is expected; simulate accept by mocking window.confirm
    window.confirm = jest.fn(() => true);

    await waitFor(() => expect(axios.delete).toHaveBeenCalled());
  });

  test('renders object list (exercises) and normalizes', async () => {
    axios.get.mockResolvedValueOnce({ data: [{ exercise_name: 'Squat' }, { exercise_name: 'Press' }] });
    axios.delete.mockResolvedValueOnce({ data: { message: 'Deleted' } });

    render(<ManageItemsPage title="Exercises" fetchUrl="/api/v1/exercises_list" deleteUrl="/api/v1/delete_exercise" />);

    await waitFor(() => expect(screen.getByText('Squat')).toBeInTheDocument());
    const deleteButtons = screen.getAllByText('Delete');
    fireEvent.click(deleteButtons[0]);
    window.confirm = jest.fn(() => true);
    await waitFor(() => expect(axios.delete).toHaveBeenCalled());
  });
});
