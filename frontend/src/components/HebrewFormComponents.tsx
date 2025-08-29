import React from 'react';
import { Box, TextField, FormControl, InputLabel, Select, Button, MenuItem, TextFieldProps, SelectProps } from '@mui/material';
import { TEXT_COLORS, INTERACTIVE_COLORS, TABLE_COLORS } from './colorSystem';

interface HebrewTextFieldProps extends Omit<TextFieldProps, 'onChange'> {
  onChange?: ((value: string) => void) | ((event: React.ChangeEvent<HTMLInputElement>) => void);
}

interface HebrewSelectProps extends Omit<SelectProps, 'children'> {
  children?: React.ReactNode;
  options?: Array<{ value: any; label: string }>;
}

// Hebrew-only TextField with RTL support
export const HebrewTextField: React.FC<HebrewTextFieldProps> = ({ onChange, ...props }) => {
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (onChange) {
      // Try calling onChange with value first (for setState functions)
      // If that fails, call with event (standard Material-UI behavior)
      try {
        onChange(event.target.value);
      } catch (error) {
        // If direct value call fails, use the event
        onChange(event);
      }
    }
  };

  return (
    <TextField
      {...props}
      onChange={handleChange}
      sx={{
        direction: 'rtl',
        textAlign: 'right',
        '& .MuiInputBase-input': {
          direction: 'rtl',
          textAlign: 'right',
          color: TEXT_COLORS.text_primary,
        },
        '& .MuiInputLabel-root': {
          direction: 'rtl',
          color: TEXT_COLORS.text_secondary,
        },
        '& .MuiOutlinedInput-notchedOutline': {
          borderColor: INTERACTIVE_COLORS.input_border,
        },
        '&:hover .MuiOutlinedInput-notchedOutline': {
          borderColor: INTERACTIVE_COLORS.input_border_focus,
        },
        '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
          borderColor: INTERACTIVE_COLORS.input_border_focus,
        },
        ...props.sx,
      }}
    />
  );
};

// Hebrew-only Select with RTL support
export const HebrewSelect: React.FC<HebrewSelectProps> = ({ children, options, ...props }) => (
  <FormControl sx={{ direction: 'rtl', minWidth: 120 }}>
    <InputLabel sx={{ direction: 'rtl', color: TEXT_COLORS.text_secondary }}>
      {props.label}
    </InputLabel>
    <Select
      {...props}
      sx={{
        direction: 'rtl',
        textAlign: 'right',
        color: TEXT_COLORS.text_primary,
        '& .MuiSelect-select': {
          direction: 'rtl',
          textAlign: 'right',
        },
        '& .MuiOutlinedInput-notchedOutline': {
          borderColor: INTERACTIVE_COLORS.input_border,
        },
        '&:hover .MuiOutlinedInput-notchedOutline': {
          borderColor: INTERACTIVE_COLORS.input_border_focus,
        },
        '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
          borderColor: INTERACTIVE_COLORS.input_border_focus,
        },
        ...props.sx,
      }}
    >
      {options ? options.map((option: any) => (
        <MenuItem key={option.value} value={option.value}>
          {option.label}
        </MenuItem>
      )) : children}
    </Select>
  </FormControl>
);

// Hebrew-only Button with RTL support
export const HebrewButton: React.FC<React.ComponentProps<typeof Button>> = (props) => (
  <Button
    {...props}
    sx={{
      direction: 'rtl',
      textAlign: 'center',
      fontWeight: 600,
      borderRadius: 2,
      textTransform: 'none',
      ...props.sx,
    }}
  />
);

// Hebrew-only Form Section with RTL support
export const HebrewFormSection: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <Box sx={{ mb: 3, direction: 'rtl' }}>
    <Box
      sx={{
        fontSize: '1.1rem',
        fontWeight: 600,
        color: TEXT_COLORS.text_primary,
        mb: 2,
        pb: 1,
        borderBottom: `2px solid ${TABLE_COLORS.table_border}`,
        textAlign: 'right',
      }}
    >
      {title}
    </Box>
    <Box sx={{ direction: 'rtl' }}>
      {children}
    </Box>
  </Box>
);