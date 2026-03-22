# Quran Donation Bot UX Flow

## Brand Direction

- Tone: trustworthy, respectful, calm, warm, and charity-focused
- UI style: premium Telegram-native chat screens with clean white cards and soft green emphasis
- Primary color: soft green
- Support accents: muted gold for warmth, pale gray-green for dividers and surfaces
- Interaction principle: one clear action per step, no crowded messages, no ambiguous navigation

## Main Navigation

Reply keyboard layout:

```text
[ Donate Quran ]
[ My Donations ] [ Settings ]
[ About Us ] [ Help ] [ Send Feedback ]
```

Notes:

- `Donate Quran` is the primary action and should be visually first.
- `Settings` replaces `My Profile`.
- `About Us`, `Help`, and `Send Feedback` stay grouped as secondary support actions.

## 1. Welcome / Start

Bot message:

```text
Assalam Alaikum [Name].
Welcome to Quran Donation Bot.
This bot is intended to help people donate Qurans for rural Muslim children in Tigray.
📖 1 Quran = 450 Birr
Thank you for your donation and support.
```

Below the message:

- Telegram updates channel link
- Main menu keyboard

UX goals:

- Establish mission immediately
- Show price early to reduce friction later
- Make the bot feel like a real donation service, not a generic chat assistant

## 2. Donate Quran Flow

Prompt:

```text
Please enter the amount of Qurans you want to donate.
```

Input behavior:

- Accept only positive whole numbers
- Reject empty, text, decimals, negative values, and zero
- Keep the user in the same step until valid input is provided

Confirmation message:

```text
The amount for [X] Quran(s) is [X * 450] Birr. Please choose a payment method.
```

Inline buttons:

```text
[ Telebirr ] [ Awash ]
[ CBE ] [ Abyssinia ]
[ Zemzem ] [ Hijra ]
[ Gadda ]
```

## 3. Payment Method Screen

Structure:

- Payment provider title
- Amount due
- Account number
- Account name
- Optional reference text
- Clear instruction to send a receipt screenshot

Message pattern:

```text
Please deposit [amount] Birr to this account and send a screenshot of the payment receipt.
```

Trust elements:

- Keep account details in a compact card-like block
- Repeat the exact amount due
- Mention that the receipt will be reviewed by admin before approval

## 4. Screenshot Submission

Waiting state:

```text
Please send a clear payment screenshot that shows the amount, date, and account destination.
```

Success after upload:

```text
Your screenshot has been sent to the admin for approval.
```

UX goals:

- Confirm that the image was received
- Make the pending-review status explicit
- Avoid leaving the user unsure whether the upload worked

## 5. Approval Success

Approved message:

```text
The admin has confirmed your screenshot. Thank you for your donation and subscription.
```

Recommended quick actions:

- `Donate Again`
- `View My Donations`

## 6. My Donations

Content:

- Total amount donated
- Total Qurans donated
- Donation history list
- Payment date
- Payment method
- Status badge: `Pending`, `Approved`, or `Rejected`

Layout approach:

- Summary card at top
- Donation cards below, one item per donation
- Most recent donation first

## 7. Settings

Settings items:

- `Language` with disabled state and `Coming Soon`
- `Payment Method` with current selected provider shown on the right
- `Quran Amount` with current default amount shown on the right

Interaction rules:

- Tapping `Payment Method` opens the same provider list used during donation
- Tapping `Quran Amount` lets the user raise or change their default amount
- `Language` is non-interactive for now

## 8. About Us

Message goals:

- Explain the mission clearly
- Describe the impact on rural Muslim children in Tigray
- Reinforce trust and charity focus

Tone:

- Respectful and concise
- Mission-driven, not promotional

## 9. Help

Include:

- How to donate
- How admin approval works
- What to do if payment review is delayed
- How to contact support or admin

Suggested support CTA:

- `Contact Admin`

## 10. Send Feedback

Prompt:

```text
Please type your feedback below. Your message will be sent directly to the admin team.
```

Confirmation:

```text
Thank you. Your feedback has been sent to the admin.
```

## 11. Error / Validation States

Invalid Quran amount:

```text
Please enter a valid number.
```

Unsupported message while waiting for receipt:

```text
Please send a payment screenshot.
```

Rejected screenshot:

```text
Your screenshot was rejected. Please resend a valid receipt.
```

General error:

```text
Something went wrong. Please try again in a moment or contact support.
```

Design rules:

- Keep errors short and polite
- Always provide an obvious recovery action
- Preserve user progress whenever possible

## Production Notes

- Use reply keyboards for navigation and inline keyboards for contextual choices
- Store the active flow state so unsupported messages can be handled correctly
- Repeat amount and selected payment method in every payment-related state
- Use status labels consistently across admin review, user history, and notifications
- Keep message bodies short enough to fit naturally inside Telegram without looking dense
