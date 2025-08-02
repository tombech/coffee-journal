const { test, expect } = require('@playwright/test');

test('debug region count display', async ({ page }) => {
  await page.goto('/settings/countries');
  
  // Wait for page to load
  await expect(page.getByRole('heading', { name: 'Countries' })).toBeVisible();
  
  // Get all table cells to see what's actually displayed
  const cells = await page.locator('td').allTextContents();
  console.log('All table cells:', cells);
  
  // Look specifically for region-related cells
  const regionCells = cells.filter(cell => cell.includes('region'));
  console.log('Region cells:', regionCells);
  
  // Check the actual structure of the table
  const tableRows = await page.locator('tr').count();
  console.log('Number of table rows:', tableRows);
  
  for (let i = 0; i < tableRows; i++) {
    const rowCells = await page.locator('tr').nth(i).locator('td').allTextContents();
    if (rowCells.length > 0) {
      console.log(`Row ${i}:`, rowCells);
    }
  }
});