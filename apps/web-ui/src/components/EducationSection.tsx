import React, { useState } from 'react';
import { 
  GraduationCap, 
  Calendar, 
  MapPin, 
  Plus,
  Edit3,
  Trash2,
  Check,
  X,
  Award,
  Book
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Education } from '../types/profile';

interface EducationSectionProps {
  education: Education[];
  onUpdateEducation: (education: Education[]) => void;
  isEditable?: boolean;
}

const EducationSection: React.FC<EducationSectionProps> = ({
  education,
  onUpdateEducation,
  isEditable = true,
}) => {
  const [isAdding, setIsAdding] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [newEducation, setNewEducation] = useState<Partial<Education>>({});
  const [editData, setEditData] = useState<Partial<Education>>({});

  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short' 
      });
    } catch {
      return dateString;
    }
  };

  const handleAdd = () => {
    if (!newEducation.institution || !newEducation.degree) return;
    
    const educationItem: Education = {
      id: `edu_${Date.now()}`,
      institution: newEducation.institution || '',
      degree: newEducation.degree || '',
      fieldOfStudy: newEducation.fieldOfStudy || '',
      startDate: newEducation.startDate,
      endDate: newEducation.endDate,
      gpa: newEducation.gpa,
      honors: newEducation.honors || [],
      activities: newEducation.activities || [],
      relevantCourses: newEducation.relevantCourses || [],
      isCurrentlyEnrolled: newEducation.isCurrentlyEnrolled || false,
      location: newEducation.location,
    };

    onUpdateEducation([...education, educationItem]);
    setNewEducation({});
    setIsAdding(false);
  };

  const handleEdit = (id: string) => {
    const educationItem = education.find(edu => edu.id === id);
    if (educationItem) {
      setEditData(educationItem);
      setEditingId(id);
    }
  };

  const handleSaveEdit = () => {
    if (!editingId) return;
    
    const updatedEducation = education.map(edu => 
      edu.id === editingId ? { ...edu, ...editData } : edu
    );
    
    onUpdateEducation(updatedEducation);
    setEditingId(null);
    setEditData({});
  };

  const handleDelete = (id: string) => {
    const updatedEducation = education.filter(edu => edu.id !== id);
    onUpdateEducation(updatedEducation);
  };

  const parseList = (text: string): string[] => {
    return text.split('\n').map(item => item.trim()).filter(item => item.length > 0);
  };

  const formatList = (list: string[]): string => {
    return list.join('\n');
  };

  const getDegreeIcon = (degree: string) => {
    const lowerDegree = degree.toLowerCase();
    if (lowerDegree.includes('phd') || lowerDegree.includes('doctorate')) {
      return <Award className="text-purple-600" size={20} />;
    } else if (lowerDegree.includes('master') || lowerDegree.includes('ms') || lowerDegree.includes('ma')) {
      return <GraduationCap className="text-blue-600" size={20} />;
    } else if (lowerDegree.includes('bachelor') || lowerDegree.includes('bs') || lowerDegree.includes('ba')) {
      return <Book className="text-green-600" size={20} />;
    }
    return <GraduationCap className="text-gray-600" size={20} />;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl shadow-lg p-6 mb-6"
    >
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-100 rounded-lg">
            <GraduationCap className="text-green-600" size={24} />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Education</h2>
            <p className="text-gray-600">Academic background and qualifications</p>
          </div>
        </div>
        
        {isEditable && (
          <button
            onClick={() => setIsAdding(true)}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Plus size={20} />
            Add Education
          </button>
        )}
      </div>

      {/* Add New Education Form */}
      <AnimatePresence>
        {isAdding && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-6 p-4 border border-gray-200 rounded-lg bg-gray-50"
          >
            <h3 className="text-lg font-semibold mb-4">Add New Education</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <input
                type="text"
                placeholder="Institution Name"
                value={newEducation.institution || ''}
                onChange={(e) => setNewEducation(prev => ({ ...prev, institution: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              />
              <input
                type="text"
                placeholder="Degree (e.g., Bachelor of Science)"
                value={newEducation.degree || ''}
                onChange={(e) => setNewEducation(prev => ({ ...prev, degree: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              />
              <input
                type="text"
                placeholder="Field of Study"
                value={newEducation.fieldOfStudy || ''}
                onChange={(e) => setNewEducation(prev => ({ ...prev, fieldOfStudy: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              />
              <input
                type="text"
                placeholder="Location"
                value={newEducation.location || ''}
                onChange={(e) => setNewEducation(prev => ({ ...prev, location: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              />
              <input
                type="month"
                placeholder="Start Date"
                value={newEducation.startDate || ''}
                onChange={(e) => setNewEducation(prev => ({ ...prev, startDate: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              />
              <input
                type="month"
                placeholder="End Date"
                value={newEducation.endDate || ''}
                onChange={(e) => setNewEducation(prev => ({ ...prev, endDate: e.target.value }))}
                disabled={newEducation.isCurrentlyEnrolled}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 disabled:bg-gray-100"
              />
              <input
                type="text"
                placeholder="GPA (optional)"
                value={newEducation.gpa || ''}
                onChange={(e) => setNewEducation(prev => ({ ...prev, gpa: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              />
              <div className="flex items-center">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={newEducation.isCurrentlyEnrolled || false}
                    onChange={(e) => setNewEducation(prev => ({ 
                      ...prev, 
                      isCurrentlyEnrolled: e.target.checked,
                      endDate: e.target.checked ? undefined : prev.endDate
                    }))}
                    className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                  />
                  <span className="text-sm text-gray-700">Currently enrolled</span>
                </label>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Honors/Awards (one per line)
                </label>
                <textarea
                  placeholder="Dean's List&#10;Magna Cum Laude&#10;Scholarship Recipient"
                  value={formatList(newEducation.honors || [])}
                  onChange={(e) => setNewEducation(prev => ({ ...prev, honors: parseList(e.target.value) }))}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Activities/Organizations (one per line)
                </label>
                <textarea
                  placeholder="Computer Science Club&#10;Student Government&#10;Debate Team"
                  value={formatList(newEducation.activities || [])}
                  onChange={(e) => setNewEducation(prev => ({ ...prev, activities: parseList(e.target.value) }))}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                />
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Relevant Coursework (one per line)
              </label>
              <textarea
                placeholder="Data Structures and Algorithms&#10;Database Systems&#10;Machine Learning"
                value={formatList(newEducation.relevantCourses || [])}
                onChange={(e) => setNewEducation(prev => ({ ...prev, relevantCourses: parseList(e.target.value) }))}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              />
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleAdd}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
              >
                <Check size={16} />
                Add Education
              </button>
              <button
                onClick={() => {
                  setIsAdding(false);
                  setNewEducation({});
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

      {/* Education List */}
      <div className="space-y-6">
        {education.length === 0 ? (
          <div className="text-center py-12">
            <GraduationCap className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No education added</h3>
            <p className="text-gray-600 mb-4">Add your educational background to showcase your qualifications</p>
            {isEditable && (
              <button
                onClick={() => setIsAdding(true)}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                Add Your First Education
              </button>
            )}
          </div>
        ) : (
          education.map((educationItem, index) => (
            <motion.div
              key={educationItem.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-gray-50 rounded-lg p-6"
            >
              {editingId === educationItem.id ? (
                /* Edit Mode */
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <input
                      type="text"
                      value={editData.institution || ''}
                      onChange={(e) => setEditData(prev => ({ ...prev, institution: e.target.value }))}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                      placeholder="Institution Name"
                    />
                    <input
                      type="text"
                      value={editData.degree || ''}
                      onChange={(e) => setEditData(prev => ({ ...prev, degree: e.target.value }))}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                      placeholder="Degree"
                    />
                    <input
                      type="text"
                      value={editData.fieldOfStudy || ''}
                      onChange={(e) => setEditData(prev => ({ ...prev, fieldOfStudy: e.target.value }))}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                      placeholder="Field of Study"
                    />
                    <input
                      type="text"
                      value={editData.gpa || ''}
                      onChange={(e) => setEditData(prev => ({ ...prev, gpa: e.target.value }))}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                      placeholder="GPA"
                    />
                  </div>
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
                    <div className="flex items-start gap-3">
                      <div className="mt-1">
                        {getDegreeIcon(educationItem.degree)}
                      </div>
                      <div>
                        <h3 className="text-xl font-semibold text-gray-900">{educationItem.degree}</h3>
                        {educationItem.fieldOfStudy && (
                          <p className="text-lg text-gray-700">{educationItem.fieldOfStudy}</p>
                        )}
                        <p className="text-lg text-blue-600 font-medium">{educationItem.institution}</p>
                      </div>
                    </div>
                    
                    {isEditable && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEdit(educationItem.id!)}
                          className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                        >
                          <Edit3 size={16} />
                        </button>
                        <button
                          onClick={() => handleDelete(educationItem.id!)}
                          className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Date, Location, and GPA */}
                  <div className="flex flex-wrap items-center gap-4 mb-4 text-sm text-gray-600">
                    <div className="flex items-center gap-1">
                      <Calendar size={14} />
                      <span>
                        {formatDate(educationItem.startDate)} - {
                          educationItem.isCurrentlyEnrolled ? 'Present' : formatDate(educationItem.endDate)
                        }
                      </span>
                    </div>
                    
                    {educationItem.location && (
                      <div className="flex items-center gap-1">
                        <MapPin size={14} />
                        <span>{educationItem.location}</span>
                      </div>
                    )}
                    
                    {educationItem.gpa && (
                      <div className="flex items-center gap-1">
                        <Award size={14} />
                        <span>GPA: {educationItem.gpa}</span>
                      </div>
                    )}
                  </div>

                  {/* Honors */}
                  {educationItem.honors && educationItem.honors.length > 0 && (
                    <div className="mb-4">
                      <h4 className="font-medium text-gray-900 mb-2">Honors & Awards:</h4>
                      <div className="flex flex-wrap gap-2">
                        {educationItem.honors.map((honor, idx) => (
                          <span
                            key={idx}
                            className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium"
                          >
                            {honor}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Activities */}
                  {educationItem.activities && educationItem.activities.length > 0 && (
                    <div className="mb-4">
                      <h4 className="font-medium text-gray-900 mb-2">Activities & Organizations:</h4>
                      <ul className="list-disc list-inside space-y-1 text-gray-700">
                        {educationItem.activities.map((activity, idx) => (
                          <li key={idx}>{activity}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Relevant Courses */}
                  {educationItem.relevantCourses && educationItem.relevantCourses.length > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Relevant Coursework:</h4>
                      <div className="flex flex-wrap gap-2">
                        {educationItem.relevantCourses.map((course, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm"
                          >
                            {course}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </motion.div>
          ))
        )}
      </div>
    </motion.div>
  );
};

export default EducationSection;