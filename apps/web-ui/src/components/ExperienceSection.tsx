import React, { useState } from 'react';
import { 
  Briefcase, 
  Calendar, 
  MapPin, 
  Plus,
  Edit3,
  Trash2,
  Check,
  X,
  Building,
  Clock
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import type { WorkExperience } from '../types/profile';

interface ExperienceSectionProps {
  experiences: WorkExperience[];
  onUpdateExperiences: (experiences: WorkExperience[]) => void;
  isEditable?: boolean;
}

const ExperienceSection: React.FC<ExperienceSectionProps> = ({
  experiences,
  onUpdateExperiences,
  isEditable = true,
}) => {
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [newExperience, setNewExperience] = useState<Partial<WorkExperience>>({});
  const [editData, setEditData] = useState<Partial<WorkExperience>>({});

  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short' 
      });
    } catch {
      return dateString; // Return as-is if parsing fails
    }
  };

  const calculateDuration = (startDate?: string, endDate?: string, isCurrent?: boolean) => {
    if (!startDate) return '';
    
    const start = new Date(startDate);
    const end = isCurrent ? new Date() : (endDate ? new Date(endDate) : new Date());
    
    const diffTime = Math.abs(end.getTime() - start.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    const years = Math.floor(diffDays / 365);
    const months = Math.floor((diffDays % 365) / 30);
    
    if (years > 0) {
      return `${years} year${years > 1 ? 's' : ''} ${months > 0 ? `${months} month${months > 1 ? 's' : ''}` : ''}`;
    }
    return `${months} month${months !== 1 ? 's' : ''}`;
  };

  const handleAdd = () => {
    if (!newExperience.company || !newExperience.position) return;
    
    const experience: WorkExperience = {
      id: `exp_${Date.now()}`,
      company: newExperience.company || '',
      position: newExperience.position || '',
      startDate: newExperience.startDate,
      endDate: newExperience.endDate,
      location: newExperience.location,
      description: newExperience.description || '',
      responsibilities: newExperience.responsibilities || [],
      achievements: newExperience.achievements || [],
      technologies: newExperience.technologies || [],
      isCurrentRole: newExperience.isCurrentRole || false,
      employmentType: newExperience.employmentType || 'full-time',
    };

    onUpdateExperiences([...experiences, experience]);
    setNewExperience({});
    setIsAdding(false);
  };

  const handleEdit = (id: string) => {
    const experience = experiences.find(exp => exp.id === id);
    if (experience) {
      setEditData(experience);
      setEditingId(id);
    }
  };

  const handleSaveEdit = () => {
    if (!editingId) return;
    
    const updatedExperiences = experiences.map(exp => 
      exp.id === editingId ? { ...exp, ...editData } : exp
    );
    
    onUpdateExperiences(updatedExperiences);
    setEditingId(null);
    setEditData({});
  };

  const handleDelete = (id: string) => {
    const updatedExperiences = experiences.filter(exp => exp.id !== id);
    onUpdateExperiences(updatedExperiences);
  };

  const parseResponsibilities = (text: string): string[] => {
    return text.split('\n').filter(line => line.trim().length > 0);
  };

  const formatResponsibilities = (responsibilities: string[]): string => {
    return responsibilities.join('\n');
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl shadow-lg p-6 mb-6"
    >
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Briefcase className="text-blue-600" size={24} />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Work Experience</h2>
            <p className="text-gray-600">Professional background and achievements</p>
          </div>
        </div>
        
        {isEditable && (
          <button
            onClick={() => setIsAdding(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus size={20} />
            Add Experience
          </button>
        )}
      </div>

      {/* Add New Experience Form */}
      <AnimatePresence>
        {isAdding && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-6 p-4 border border-gray-200 rounded-lg bg-gray-50"
          >
            <h3 className="text-lg font-semibold mb-4">Add New Experience</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <input
                type="text"
                placeholder="Company Name"
                value={newExperience.company || ''}
                onChange={(e) => setNewExperience(prev => ({ ...prev, company: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <input
                type="text"
                placeholder="Job Title"
                value={newExperience.position || ''}
                onChange={(e) => setNewExperience(prev => ({ ...prev, position: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <input
                type="text"
                placeholder="Location"
                value={newExperience.location || ''}
                onChange={(e) => setNewExperience(prev => ({ ...prev, location: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <select
                value={newExperience.employmentType || 'full-time'}
                onChange={(e) => setNewExperience(prev => ({ ...prev, employmentType: e.target.value as any }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="full-time">Full-time</option>
                <option value="part-time">Part-time</option>
                <option value="contract">Contract</option>
                <option value="internship">Internship</option>
                <option value="freelance">Freelance</option>
              </select>
              <input
                type="month"
                placeholder="Start Date"
                value={newExperience.startDate || ''}
                onChange={(e) => setNewExperience(prev => ({ ...prev, startDate: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <input
                type="month"
                placeholder="End Date"
                value={newExperience.endDate || ''}
                onChange={(e) => setNewExperience(prev => ({ ...prev, endDate: e.target.value }))}
                disabled={newExperience.isCurrentRole}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              />
            </div>
            <div className="mb-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={newExperience.isCurrentRole || false}
                  onChange={(e) => setNewExperience(prev => ({ 
                    ...prev, 
                    isCurrentRole: e.target.checked,
                    endDate: e.target.checked ? undefined : prev.endDate
                  }))}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">I currently work here</span>
              </label>
            </div>
            <textarea
              placeholder="Job description and responsibilities (one per line)"
              value={newExperience.description || ''}
              onChange={(e) => setNewExperience(prev => ({ ...prev, description: e.target.value }))}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 mb-4"
            />
            <div className="flex gap-2">
              <button
                onClick={handleAdd}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
              >
                <Check size={16} />
                Add Experience
              </button>
              <button
                onClick={() => {
                  setIsAdding(false);
                  setNewExperience({});
                }}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center gap-2"
              >
                <X size={16} />
                Cancel
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Experience Timeline */}
      <div className="space-y-6">
        {experiences.length === 0 ? (
          <div className="text-center py-12">
            <Briefcase className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No work experience added</h3>
            <p className="text-gray-600 mb-4">Add your professional experience to showcase your background</p>
            {isEditable && (
              <button
                onClick={() => setIsAdding(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Add Your First Experience
              </button>
            )}
          </div>
        ) : (
          experiences.map((experience, index) => (
            <motion.div
              key={experience.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="relative"
            >
              {/* Timeline line */}
              {index < experiences.length - 1 && (
                <div className="absolute left-6 top-16 w-0.5 h-full bg-gray-200 -z-10" />
              )}
              
              <div className="flex gap-4">
                {/* Timeline dot */}
                <div className="flex-shrink-0 w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
                  <Building className="text-white" size={20} />
                </div>
                
                {/* Content */}
                <div className="flex-1 bg-gray-50 rounded-lg p-6">
                  {editingId === experience.id ? (
                    /* Edit Mode */
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <input
                          type="text"
                          value={editData.company || ''}
                          onChange={(e) => setEditData(prev => ({ ...prev, company: e.target.value }))}
                          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                          placeholder="Company Name"
                        />
                        <input
                          type="text"
                          value={editData.position || ''}
                          onChange={(e) => setEditData(prev => ({ ...prev, position: e.target.value }))}
                          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                          placeholder="Job Title"
                        />
                      </div>
                      <textarea
                        value={editData.description || ''}
                        onChange={(e) => setEditData(prev => ({ ...prev, description: e.target.value }))}
                        rows={4}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="Job description"
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={handleSaveEdit}
                          className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700 transition-colors"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => {
                            setEditingId(null);
                            setEditData({});
                          }}
                          className="px-3 py-1 bg-gray-600 text-white rounded text-sm hover:bg-gray-700 transition-colors"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    /* Display Mode */
                    <>
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h3 className="text-xl font-semibold text-gray-900">{experience.position}</h3>
                          <p className="text-lg text-blue-600 font-medium">{experience.company}</p>
                        </div>
                        
                        {isEditable && (
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleEdit(experience.id!)}
                              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                            >
                              <Edit3 size={16} />
                            </button>
                            <button
                              onClick={() => handleDelete(experience.id!)}
                              className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        )}
                      </div>

                      {/* Date and Location */}
                      <div className="flex flex-wrap items-center gap-4 mb-4 text-sm text-gray-600">
                        <div className="flex items-center gap-1">
                          <Calendar size={14} />
                          <span>
                            {formatDate(experience.startDate)} - {
                              experience.isCurrentRole ? 'Present' : formatDate(experience.endDate)
                            }
                          </span>
                        </div>
                        
                        {calculateDuration(experience.startDate, experience.endDate, experience.isCurrentRole) && (
                          <div className="flex items-center gap-1">
                            <Clock size={14} />
                            <span>{calculateDuration(experience.startDate, experience.endDate, experience.isCurrentRole)}</span>
                          </div>
                        )}
                        
                        {experience.location && (
                          <div className="flex items-center gap-1">
                            <MapPin size={14} />
                            <span>{experience.location}</span>
                          </div>
                        )}
                        
                        {experience.employmentType && (
                          <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium capitalize">
                            {experience.employmentType.replace('-', ' ')}
                          </span>
                        )}
                      </div>

                      {/* Description */}
                      {experience.description && (
                        <div className="mb-4">
                          <p className="text-gray-700 whitespace-pre-line">{experience.description}</p>
                        </div>
                      )}

                      {/* Responsibilities */}
                      {experience.responsibilities && experience.responsibilities.length > 0 && (
                        <div className="mb-4">
                          <h4 className="font-medium text-gray-900 mb-2">Key Responsibilities:</h4>
                          <ul className="list-disc list-inside space-y-1 text-gray-700">
                            {experience.responsibilities.map((responsibility, idx) => (
                              <li key={idx}>{responsibility}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Technologies */}
                      {experience.technologies && experience.technologies.length > 0 && (
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2">Technologies Used:</h4>
                          <div className="flex flex-wrap gap-2">
                            {experience.technologies.map((tech, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-1 bg-gray-200 text-gray-700 rounded-full text-xs"
                              >
                                {tech}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </motion.div>
  );
};

export default ExperienceSection;