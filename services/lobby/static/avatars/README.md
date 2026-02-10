# Avatar Images

This directory contains avatar images that users can select for their profiles.

## Available Avatars

Place avatar images here with the following naming convention:
- `chips.png` - Poker chips (default)
- `spades.png` - Spade suit
- `hearts.png` - Heart suit
- `diamonds.png` - Diamond suit
- `clubs.png` - Club suit
- `ace.png` - Ace card
- `king.png` - King card
- `queen.png` - Queen card
- `jack.png` - Jack card
- `dealer.png` - Dealer button

## Format

- Recommended size: 128x128 or 256x256 pixels
- Format: PNG with transparency
- Keep file sizes small (<50KB) for fast loading

## Adding New Avatars

1. Add the image file to this directory
2. Update the avatar list in the backend API
3. The avatar_id in the database should match the filename (without extension)
