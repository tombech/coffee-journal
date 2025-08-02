import React from 'react'
import DeleteConfirmationModal from './DeleteConfirmationModal'

// Mock fetch for API calls
beforeEach(() => {
  cy.stub(window, 'fetch').as('fetchStub')
})

describe('DeleteConfirmationModal Component', () => {
  const mockOnClose = cy.stub()
  const mockOnDeleteConfirmed = cy.stub()
  
  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    item: { id: 1, name: 'Test Item' },
    itemType: 'Test Type',
    apiEndpoint: 'test-endpoint',
    usageInfo: { in_use: false, usage_count: 0, usage_type: null },
    onDeleteConfirmed: mockOnDeleteConfirmed,
    availableReplacements: []
  }

  beforeEach(() => {
    mockOnClose.reset()
    mockOnDeleteConfirmed.reset()
  })

  describe('Not In Use Scenarios', () => {
    it('shows simple confirmation when item not in use', () => {
      cy.mount(<DeleteConfirmationModal {...defaultProps} />)

      cy.contains('Delete Test Type: "Test Item"').should('be.visible')
      cy.contains(/Are you sure you want to delete "Test Item"\? This action cannot be undone./).should('be.visible')
      
      // These are the EXACT selectors that failed in Jest but work in Cypress!
      cy.get('[role="button"]').contains('Delete').should('be.visible')
      cy.get('[role="button"]').contains('Cancel').should('be.visible')
    })

    it('deletes item when not in use', () => {
      const resolvedPromise = cy.stub().resolves()
      mockOnDeleteConfirmed.returns(resolvedPromise)
      
      cy.mount(<DeleteConfirmationModal {...defaultProps} onDeleteConfirmed={mockOnDeleteConfirmed} />)

      cy.get('[role="button"]').contains('Delete').click()

      cy.then(() => {
        expect(mockOnDeleteConfirmed).to.have.been.called
        expect(mockOnClose).to.have.been.called
      })
    })

    it('closes modal when cancel clicked', () => {
      cy.mount(<DeleteConfirmationModal {...defaultProps} onClose={mockOnClose} />)

      cy.get('[role="button"]').contains('Cancel').click()

      cy.then(() => {
        expect(mockOnClose).to.have.been.called
        expect(mockOnDeleteConfirmed).not.to.have.been.called
      })
    })

    it('closes modal when clicking backdrop', () => {
      cy.mount(<DeleteConfirmationModal {...defaultProps} onClose={mockOnClose} />)

      // Click the backdrop (outer div) - need to click outside the modal content
      cy.get('body').click(0, 0)

      cy.then(() => {
        expect(mockOnClose).to.have.been.called
      })
    })
  })

  describe('In Use Scenarios', () => {
    const inUseProps = {
      ...defaultProps,
      usageInfo: { in_use: true, usage_count: 5, usage_type: 'products' },
      availableReplacements: [
        { id: 2, name: 'Replacement Item 1' },
        { id: 3, name: 'Replacement Item 2' }
      ]
    }

    it('shows usage warning and options when item in use', () => {
      cy.mount(<DeleteConfirmationModal {...inUseProps} />)

      cy.contains(/This test type is currently being used in 5 products/).should('be.visible')
      cy.contains('Choose how to proceed:').should('be.visible')
      
      // Use semantic selectors for radio buttons
      cy.get('[role="radio"]').contains('Cancel deletion').should('be.visible')
      cy.get('[role="radio"]').contains('Remove all references and delete').should('be.visible')
      cy.get('[role="radio"]').contains('Replace with another test type and delete').should('be.visible')
    })

    it('shows correct usage description for single item', () => {
      const singleUseProps = {
        ...inUseProps,
        usageInfo: { in_use: true, usage_count: 1, usage_type: 'brew_sessions' }
      }

      cy.mount(<DeleteConfirmationModal {...singleUseProps} />)

      cy.contains(/This test type is currently being used in 1 brew session/).should('be.visible')
    })

    it('cancel option is selected by default', () => {
      cy.mount(<DeleteConfirmationModal {...inUseProps} />)

      // Check that cancel radio is selected by default
      cy.get('input[value="cancel"]').should('be.checked')

      // Confirm button should show appropriate text and be disabled
      cy.get('[role="button"]').contains('Choose an option above').should('be.disabled')
    })

    it('removes references when remove option selected', () => {
      const resolvedPromise = cy.stub().resolves()
      mockOnDeleteConfirmed.returns(resolvedPromise)
      
      // Mock the API call
      cy.get('@fetchStub').resolves({
        ok: true,
        json: cy.stub().resolves({ message: 'References removed' })
      })

      cy.mount(<DeleteConfirmationModal {...inUseProps} onDeleteConfirmed={mockOnDeleteConfirmed} />)

      // Select remove references option
      cy.get('input[value="remove_references"]').check()
      
      // Confirm button should be enabled with correct text
      cy.get('[role="button"]').contains('Remove References & Delete').should('be.enabled')
      cy.get('[role="button"]').contains('Remove References & Delete').click()

      cy.then(() => {
        expect(window.fetch).to.have.been.calledWithMatch(
          Cypress.sinon.match(/\/test-endpoint\/1\/update_references$/),
          Cypress.sinon.match({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'remove', replacement_id: null })
          })
        )
        expect(mockOnDeleteConfirmed).to.have.been.called
        expect(mockOnClose).to.have.been.called
      })
    })

    it('shows replacement dropdown when replace option selected', () => {
      cy.mount(<DeleteConfirmationModal {...inUseProps} />)

      cy.get('input[value="replace_references"]').check()

      // Check that select dropdown appears
      cy.get('select').should('be.visible')
      cy.get('select option').contains('Select replacement...').should('exist')

      // Should not include the item being deleted
      cy.get('select option').contains('Replacement Item 1').should('exist')
      cy.get('select option').contains('Replacement Item 2').should('exist')
      cy.get('select option').contains('Test Item').should('not.exist')
    })

    it('disables confirm until replacement selected', () => {
      cy.mount(<DeleteConfirmationModal {...inUseProps} />)

      cy.get('input[value="replace_references"]').check()

      // Initially disabled
      cy.get('[role="button"]').contains('Replace & Delete').should('be.disabled')

      // Select a replacement
      cy.get('select').select('2')

      // Should be enabled now
      cy.get('[role="button"]').contains('Replace & Delete').should('be.enabled')
    })

    it('replaces references when replace option confirmed', () => {
      const resolvedPromise = cy.stub().resolves()
      mockOnDeleteConfirmed.returns(resolvedPromise)
      
      // Mock the API call
      cy.get('@fetchStub').resolves({
        ok: true,
        json: cy.stub().resolves({ message: 'References replaced' })
      })

      cy.mount(<DeleteConfirmationModal {...inUseProps} onDeleteConfirmed={mockOnDeleteConfirmed} />)

      cy.get('input[value="replace_references"]').check()
      cy.get('select').select('3')
      cy.get('[role="button"]').contains('Replace & Delete').click()

      cy.then(() => {
        expect(window.fetch).to.have.been.calledWithMatch(
          Cypress.sinon.match(/\/test-endpoint\/1\/update_references$/),
          Cypress.sinon.match({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'replace', replacement_id: '3' })
          })
        )
        expect(mockOnDeleteConfirmed).to.have.been.called
        expect(mockOnClose).to.have.been.called
      })
    })

    it('hides replace option when no replacements available', () => {
      const noReplacementsProps = {
        ...inUseProps,
        availableReplacements: []
      }

      cy.mount(<DeleteConfirmationModal {...noReplacementsProps} />)

      cy.get('[role="radio"]').contains('Cancel deletion').should('be.visible')
      cy.get('[role="radio"]').contains('Remove all references and delete').should('be.visible')
      cy.get('[role="radio"]').contains('Replace with another test type and delete').should('not.exist')
    })
  })

  describe('Error Handling', () => {
    it('shows error when update references fails', () => {
      // Mock window.alert
      cy.stub(window, 'alert').as('alertStub')
      
      // Mock fetch to reject
      cy.get('@fetchStub').rejects(new Error('Network error'))

      const props = {
        ...defaultProps,
        usageInfo: { in_use: true, usage_count: 2, usage_type: 'products' }
      }

      cy.mount(<DeleteConfirmationModal {...props} />)

      cy.get('input[value="remove_references"]').check()
      cy.get('[role="button"]').contains('Remove References & Delete').click()

      cy.get('@alertStub').should('have.been.calledWith', 'Error: Network error')
      
      cy.then(() => {
        expect(mockOnDeleteConfirmed).not.to.have.been.called
        expect(mockOnClose).not.to.have.been.called
      })
    })

    it('shows processing state during operation', () => {
      // Create a promise that we can control
      let resolvePromise
      const controlledPromise = new Promise(resolve => {
        resolvePromise = resolve
      })
      mockOnDeleteConfirmed.returns(controlledPromise)
      
      cy.mount(<DeleteConfirmationModal {...defaultProps} onDeleteConfirmed={mockOnDeleteConfirmed} />)

      cy.get('[role="button"]').contains('Delete').click()

      // Should show processing state
      cy.get('[role="button"]').contains('Processing...').should('be.visible')
      cy.get('[role="button"]').contains('Cancel').should('be.disabled')

      // Resolve the promise to complete the operation
      cy.then(() => {
        resolvePromise()
      })

      cy.then(() => {
        expect(mockOnClose).to.have.been.called
      })
    })
  })

  describe('Edge Cases', () => {
    it('does not render when not open', () => {
      const closedProps = { ...defaultProps, isOpen: false }
      
      cy.mount(<DeleteConfirmationModal {...closedProps} />)
      
      // Modal should not be visible
      cy.get('body').should('not.contain', 'Delete Test Type: "Test Item"')
    })

    it('does not render when item is null', () => {
      const noItemProps = { ...defaultProps, item: null }
      
      cy.mount(<DeleteConfirmationModal {...noItemProps} />)
      
      // Modal should not be visible
      cy.get('body').should('not.contain', 'Delete Test Type')
    })

    it('handles unknown usage types', () => {
      const unknownUsageProps = {
        ...defaultProps,
        usageInfo: { in_use: true, usage_count: 3, usage_type: 'custom_type' }
      }

      cy.mount(<DeleteConfirmationModal {...unknownUsageProps} />)

      cy.contains(/This test type is currently being used in 3 custom type/).should('be.visible')
    })
  })
})