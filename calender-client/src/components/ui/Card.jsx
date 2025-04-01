// src/components/ui/Card.jsx
import React from 'react';

export const Card = ({ children }) => {
  return <div className="bg-white shadow-md rounded-lg p-4">{children}</div>;
};

export const CardHeader = ({ children }) => {
  return <div className="font-semibold text-lg mb-2">{children}</div>;
};

export const CardTitle = ({ children }) => {
  return <h3 className="text-xl font-semibold mb-4">{children}</h3>;
};

export const CardContent = ({ children }) => {
  return <div className="text-gray-700 mb-4">{children}</div>;
};

export const CardFooter = ({ children }) => {
  return <div className="text-right text-sm text-gray-500">{children}</div>;
};
