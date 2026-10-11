import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Sprout, Home } from 'lucide-react';

export const NotFound: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] max-w-md mx-auto text-center px-4">
      <Card elevated className="w-full flex flex-col items-center py-12 px-6">
        <div className="w-16 h-16 rounded-full bg-[#BFE0C8]/40 text-[#2F533B] flex items-center justify-center mb-4">
          <Sprout className="w-8 h-8" />
        </div>
        <h1 className="text-2xl font-extrabold text-[#26362F] mb-2">Page Not Found</h1>
        <p className="text-sm text-[#5F6F68] mb-6 leading-relaxed">
          The requested page could not be located. Let's return to your crop overview.
        </p>
        <Button
          variant="primary"
          leftIcon={<Home className="w-4 h-4" />}
          onClick={() => navigate('/')}
        >
          Return Home
        </Button>
      </Card>
    </div>
  );
};
