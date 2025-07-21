import React, { useState } from 'react';
import { 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  Linkedin, 
  Github, 
  Globe,
  Edit3,
  Check,
  X,
  Camera
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import type { PersonalInfo } from '../types/profile';

interface ProfileHeaderProps {
  personalInfo: PersonalInfo;
  onUpdatePersonalInfo: (info: PersonalInfo) => void;
  isEditable?: boolean;
}

const ProfileHeader: React.FC<ProfileHeaderProps> = ({
  personalInfo,
  onUpdatePersonalInfo,
  isEditable = true,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState<PersonalInfo>(personalInfo);

  const handleSave = () => {
    onUpdatePersonalInfo(editData);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditData(personalInfo);
    setIsEditing(false);
  };

  const handleInputChange = (field: keyof PersonalInfo, value: string) => {
    setEditData(prev => ({ ...prev, [field]: value }));
  };

  const getInitials = (name?: string) => {
    if (!name) return 'U';
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const formatLocation = () => {
    const parts = [personalInfo.city, personalInfo.state, personalInfo.country].filter(Boolean);
    return parts.join(', ');
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl shadow-lg p-8 mb-6 relative overflow-hidden"
    >
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50" />
      
      {/* Content */}
      <div className="relative z-10">
        <div className="flex flex-col lg:flex-row items-center lg:items-start gap-6">
          {/* Profile Picture */}
          <div className="relative group">
            <div className="w-32 h-32 rounded-full bg-gradient-to-br from-blue-500 to-blue-800 flex items-center justify-center text-white text-3xl font-bold shadow-lg">
              {getInitials(personalInfo.fullName)}
            </div>
            {isEditable && (
              <button className="absolute bottom-2 right-2 bg-white rounded-full p-2 shadow-lg opacity-0 group-hover:opacity-100 transition-opacity">
                <Camera size={16} className="text-gray-600" />
              </button>
            )}
          </div>

          {/* Main Info */}
          <div className="flex-1 text-center lg:text-left">
            {!isEditing ? (
              <>
                <div className="flex items-center justify-center lg:justify-start gap-3 mb-2">
                  <h1 className="text-3xl font-bold text-gray-900">
                    {personalInfo.fullName || 'Handsome User'}
                  </h1>
                  {isEditable && (
                    <button
                      onClick={() => setIsEditing(true)}
                      className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      <Edit3 size={20} />
                    </button>
                  )}
                </div>

                {personalInfo.professionalSummary && (
                  <p className="text-lg text-gray-600 mb-4 max-w-2xl">
                    {personalInfo.professionalSummary}
                  </p>
                )}

                {personalInfo.objective && !personalInfo.professionalSummary && (
                  <p className="text-lg text-gray-600 mb-4 max-w-2xl">
                    {personalInfo.objective}
                  </p>
                )}

                {/* Contact Info Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
                  {personalInfo.email && (
                    <div className="flex items-center gap-2 text-gray-600">
                      <Mail size={18} className="text-blue-500" />
                      <span>{personalInfo.email}</span>
                    </div>
                  )}

                  {personalInfo.phone && (
                    <div className="flex items-center gap-2 text-gray-600">
                      <Phone size={18} className="text-green-500" />
                      <span>{personalInfo.phone}</span>
                    </div>
                  )}

                  {formatLocation() && (
                    <div className="flex items-center gap-2 text-gray-600">
                      <MapPin size={18} className="text-red-500" />
                      <span>{formatLocation()}</span>
                    </div>
                  )}

                  {personalInfo.linkedin && (
                    <div className="flex items-center gap-2">
                      <Linkedin size={18} className="text-blue-600" />
                      <a
                        href={personalInfo.linkedin}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 transition-colors"
                      >
                        LinkedIn Profile
                      </a>
                    </div>
                  )}

                  {personalInfo.github && (
                    <div className="flex items-center gap-2">
                      <Github size={18} className="text-gray-800" />
                      <a
                        href={personalInfo.github}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-gray-800 hover:text-gray-600 transition-colors"
                      >
                        GitHub Profile
                      </a>
                    </div>
                  )}

                  {personalInfo.website && (
                    <div className="flex items-center gap-2">
                      <Globe size={18} className="text-purple-500" />
                      <a
                        href={personalInfo.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-purple-600 hover:text-purple-800 transition-colors"
                      >
                        Personal Website
                      </a>
                    </div>
                  )}
                </div>
              </>
            ) : (
              /* Edit Mode */
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-4"
              >
                <div className="flex items-center gap-3 mb-4">
                  <h2 className="text-xl font-semibold text-gray-900">Edit Profile Information</h2>
                  <div className="flex gap-2">
                    <button
                      onClick={handleSave}
                      className="px-3 py-1 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-1"
                    >
                      <Check size={16} />
                      Save
                    </button>
                    <button
                      onClick={handleCancel}
                      className="px-3 py-1 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center gap-1"
                    >
                      <X size={16} />
                      Cancel
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Full Name
                    </label>
                    <input
                      type="text"
                      value={editData.fullName || ''}
                      onChange={(e) => handleInputChange('fullName', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Enter your full name"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Email
                    </label>
                    <input
                      type="email"
                      value={editData.email || ''}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Enter your email"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Phone
                    </label>
                    <input
                      type="tel"
                      value={editData.phone || ''}
                      onChange={(e) => handleInputChange('phone', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Enter your phone number"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      City
                    </label>
                    <input
                      type="text"
                      value={editData.city || ''}
                      onChange={(e) => handleInputChange('city', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Enter your city"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      LinkedIn URL
                    </label>
                    <input
                      type="url"
                      value={editData.linkedin || ''}
                      onChange={(e) => handleInputChange('linkedin', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="https://linkedin.com/in/yourprofile"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      GitHub URL
                    </label>
                    <input
                      type="url"
                      value={editData.github || ''}
                      onChange={(e) => handleInputChange('github', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="https://github.com/yourusername"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Professional Summary
                  </label>
                  <textarea
                    value={editData.professionalSummary || ''}
                    onChange={(e) => handleInputChange('professionalSummary', e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Brief summary of your professional background and goals"
                  />
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default ProfileHeader;