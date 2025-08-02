import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import StarRating from '../StarRating';

describe('StarRating Bug Tests', () => {
  test('should save rating changes when clicking stars (demonstrating bug)', () => {
    let savedRating = '';  // Simulating empty initial rating from form state
    const mockOnRatingChange = jest.fn((rating) => {
      savedRating = rating;
    });

    const { rerender } = render(
      <StarRating
        rating={savedRating}
        onRatingChange={mockOnRatingChange}
        maxRating={5}
        size="medium"
      />
    );

    // Click on the 3rd star to give a rating of 3
    const stars = screen.getAllByText(/★|☆/);
    fireEvent.click(stars[2]); // Click 3rd star (0-indexed)

    // Verify the callback was called with rating 3
    expect(mockOnRatingChange).toHaveBeenCalledWith(3);
    expect(savedRating).toBe(3);

    // Rerender with new rating to simulate component update
    rerender(
      <StarRating
        rating={savedRating}
        onRatingChange={mockOnRatingChange}
        maxRating={5}
        size="medium"
      />
    );

    // The component should now show 3 stars filled
    // This is where the bug occurs - empty string rating might not render correctly
    const filledStars = screen.getAllByText('★');
    expect(filledStars).toHaveLength(3);
  });

  test('should handle empty string rating gracefully', () => {
    const mockOnRatingChange = jest.fn();

    // This simulates the bug - when rating is empty string from form state
    render(
      <StarRating
        rating=""  // Empty string from form state
        onRatingChange={mockOnRatingChange}
        maxRating={5}
        size="medium"
      />
    );

    // Should render 5 empty stars
    const emptyStars = screen.getAllByText('☆');
    expect(emptyStars).toHaveLength(5);

    // Click should still work
    fireEvent.click(emptyStars[0]);
    expect(mockOnRatingChange).toHaveBeenCalledWith(1);
  });

  test('should handle null rating gracefully', () => {
    const mockOnRatingChange = jest.fn();

    render(
      <StarRating
        rating={null}  // null from backend after safe_int conversion
        onRatingChange={mockOnRatingChange}
        maxRating={5}
        size="medium"
      />
    );

    // Should render 5 empty stars
    const emptyStars = screen.getAllByText('☆');
    expect(emptyStars).toHaveLength(5);

    // Click should still work
    fireEvent.click(emptyStars[0]);
    expect(mockOnRatingChange).toHaveBeenCalledWith(1);
  });

  test('should handle undefined rating gracefully', () => {
    const mockOnRatingChange = jest.fn();

    render(
      <StarRating
        rating={undefined}  // undefined rating
        onRatingChange={mockOnRatingChange}
        maxRating={5}
        size="medium"
      />
    );

    // Should render 5 empty stars
    const emptyStars = screen.getAllByText('☆');
    expect(emptyStars).toHaveLength(5);

    // Click should still work
    fireEvent.click(emptyStars[0]);
    expect(mockOnRatingChange).toHaveBeenCalledWith(1);
  });
});