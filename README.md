# Octo Auto Routing & Split Bill

## Overview

Octo Auto Routing & Split Bill is a mobile banking companion concept for CIMB Niaga Octo Mobile that reduces repetitive manual input in two common scenarios:

1. Auto routing from shared content into a prefilled transaction form.
2. Split bill management with OCR, shared expense tracking, and one-tap settlement.

The goal is to make payment actions faster, more accurate, and less frustrating for users who frequently receive payment requests or need to divide expenses with friends, family, or teammates.

## Problem Statement

Today, users often need to manually copy payment details from social media, chat apps, gallery images, or other apps into their banking app. This takes time and increases the chance of errors.

Split bills are also usually handled outside the bank, using spreadsheets, calculators, screenshots, or chat messages. That creates confusion when multiple people buy different items, when tax and service charges must be shared, or when one person pays first and waits to be reimbursed later.

This product is designed to simplify both workflows.

## Core Idea

The application focuses on two major experiences:

### 1. Auto Routing

When a user taps Share from WhatsApp, social media, gallery, or any other application, they can choose Octo Mobile as the destination. The app reads the shared content, identifies payment information, and opens a transaction form that is automatically filled as much as possible.

The user only needs to confirm the details and enter their password to complete the transaction.

### 2. Split Bill

The user enters or scans a bill using OCR. The app extracts items, totals, taxes, and other charges. It then creates a shared group where everyone involved can assign items to themselves.

Each person can mark what they purchased, and the app will calculate the final amount automatically. When settlement is ready, the person who paid first can send transfer requests to others without manually entering amounts over and over again. The recipient only needs to confirm and pay.

## Key Features

### Auto Routing

- Accept shared content from WhatsApp, social media, image gallery, notes, email, or any app that supports sharing.
- Detect payment-related data such as account numbers, bank names, amount, reference text, and notes.
- Auto-fill the transaction form in Octo Mobile.
- Reduce manual typing and copy-paste errors.
- Require final user confirmation before transfer.

### Split Bill

- Scan bills with OCR.
- Extract line items, totals, taxes, and service charges.
- Create a bill group for friends, coworkers, or family.
- Let users assign items to specific people.
- Automatically divide shared costs such as tax and service fee.
- Generate settlement amounts for each participant.
- Create payment links or transfer actions for quick reimbursement.
- Show clear status for who has paid, who still owes money, and what remains unresolved.

## Auto Routing Flow

1. A user sees payment information in another app.
2. The user taps Share.
3. Octo Mobile appears as a destination option.
4. The app reads the shared content.
5. The transaction form is populated automatically.
6. The user reviews the details.
7. The user enters their password and confirms the transfer.

### Example Use Cases

- A friend sends bank details in WhatsApp.
- A seller posts payment instructions on social media.
- A screenshot in the gallery contains account number and amount.
- A user copies payment text from email and wants to pay immediately.

## Split Bill Flow

1. The user uploads or scans a receipt or bill.
2. OCR extracts the bill content.
3. The app identifies items, subtotal, tax, and other charges.
4. The user creates a group and invites friends.
5. Each participant selects the items they ordered.
6. The app distributes shared charges automatically.
7. The app calculates how much each person owes.
8. Settlement requests are generated.
9. The paying user transfers money with minimal manual input.
10. Each recipient only confirms the payment.

## Split Bill Logic

The split bill system is designed to support real-world dining and group spending scenarios.

### Item Ownership

Users can assign one or more menu items to a specific participant. This is useful when different people order different food or drinks.

### Shared Charges

Tax, service fee, and other common charges are divided automatically across the group based on the chosen split method.

### Flexible Splitting

The app can support different split strategies, such as:

- Equal split for shared items.
- Item-based split for personalized orders.
- Mixed split for both shared and individual items.

### Settlement

After the bill is finalized, the app calculates each participant’s balance and provides a quick way to transfer the exact amount to the person who paid upfront.

## User Benefits

- Less manual typing.
- Faster payment completion.
- Lower risk of transfer mistakes.
- Better visibility for group expenses.
- Easier reimbursement between friends or coworkers.
- Cleaner mobile banking experience.

## Product Principles

- Reduce friction before payment.
- Keep the user in control.
- Confirm all sensitive actions explicitly.
- Make split payments understandable at a glance.
- Avoid forcing users to re-enter information that can be inferred safely.

## Suggested Product Scope

### MVP

- Share-to-app transaction prefill.
- OCR for receipt scanning.
- Basic split bill group creation.
- Manual item assignment.
- Automatic tax and service charge splitting.
- Transfer summary and confirmation screen.

### Future Enhancements

- Smart OCR cleanup for blurry receipts.
- Suggested item detection by participant.
- Reusable group templates for recurring meals or trips.
- Payment reminders for unpaid balances.
- Expense history and analytics.
- Partial settlement support.

## Security And Trust

Because this application handles financial actions, the experience should always prioritize safety:

- Show a clear summary before transfer.
- Require user confirmation before any money movement.
- Protect sensitive data with secure storage and encryption.
- Validate extracted OCR data before calculation.
- Allow users to edit parsed values before final settlement.

## Example Scenario

### Shared Payment

Maria receives a payment instruction in WhatsApp. Instead of copying the details manually, she taps Share and sends the content into Octo Mobile. The app fills in the destination bank, account number, amount, and note automatically. Maria checks the summary, enters her password, and completes the transfer.

### Group Dinner Split

A group of five friends eats together. One person pays the bill first. They scan the receipt in the app, create a group, and assign each menu item to the correct person. Tax and service charges are distributed automatically. The app shows exactly how much each person owes. The paying friend sends settlement requests, and the others confirm and pay back with minimal effort.

## Project Status

This README describes the product vision and functional concept for the application. If you want, the next step can be to turn this into a more formal project README with installation steps, architecture notes, API details, or a polished product brief.

