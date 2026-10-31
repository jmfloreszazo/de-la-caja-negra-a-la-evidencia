# Synthetic, owner-unapproved executable-contract examples.
# Actual program run: run_contract.py -> .NET candidate -> independent Python oracle.
Feature: Transfer and booked-balance capabilities for a clean-room rewrite
  Background:
    Given account A has 10000 minor units and account B has 5000

  Scenario: A valid transfer conserves money
    When authorized operation TX-1 transfers 2000 from A to B
    Then the response is APPLIED
    And booked balances are A=8000 and B=7000
    And operation TX-1 has two balanced postings and exactly one outbox record

  Scenario: A duplicate operation ID has only one financial effect
    Given TX-1 has already been applied
    When the identical TX-1 is repeated
    Then the response is DUPLICATE_APPLIED
    And there is no second debit or outbox entry

  Scenario: A changed command cannot reuse an operation ID
    Given TX-1 has already been applied
    When TX-1 is repeated with a different amount
    Then the response is ID_CONFLICT
    And booked balances remain unchanged

  Scenario: An unauthorized request does not alter the ledger
    When a request to transfer 500 is marked unauthorized
    Then the response is REJECTED_UNAUTHORIZED
    And no postings or outbox are written

  Scenario: A lost reply does not imply a rollback
    When operation TX-4 transfers 1000 and its reply is deliberately lost after in-memory apply
    Then the observed response is UNKNOWN_AFTER_APPLY
    And a replay of the same operation ID returns DUPLICATE_APPLIED
    And only one in-memory financial effect exists

  Scenario: A lagging projection is not an authoritative balance
    Given the authoritative ledger version is 2 and projection version is 0
    When account A requests a projection with minimum version 2
    Then the response is STALE_PROJECTION
    And an explicit projection update makes version 2 readable
    But the projected balance is not authorized available funds
