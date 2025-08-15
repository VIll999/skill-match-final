import React from 'react';
import { motion } from 'framer-motion';
import { Briefcase, BookOpen, Trophy, LayoutDashboard } from 'lucide-react';

interface SidebarProps {
  activeItem?: string;
}

const Sidebar: React.FC<SidebarProps> = ({ activeItem = 'career-tracker' }) => {
  const menuItems = [
    { id: 'career-tracker', label: 'Career Tracker', icon: Briefcase },
    { id: 'my-books', label: 'My Books', icon: BookOpen },
    { id: 'my-achievement', label: 'My Achievement', icon: Trophy },
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  ];

  return (
    <div className="fixed left-0 top-0 bottom-0 w-[61px] bg-white shadow-[0px_4px_6px_rgba(0,0,0,0.1)] z-50">
      {/* Top Add Icon */}
      <div className="absolute top-7 left-[19px]">
        <svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M11.0155 0C9.57297 0 8.14459 0.284511 6.81189 0.837288C5.47918 1.39007 4.26826 2.20028 3.24825 3.22168C1.18826 5.28449 0.0309614 8.08226 0.0309614 10.9995C0.0213585 13.5394 0.899609 16.0027 2.51346 17.9622L0.316559 20.1621C0.16414 20.3168 0.0608899 20.5132 0.0198362 20.7266C-0.0212174 20.94 0.0017651 21.1607 0.0858839 21.3611C0.177119 21.559 0.325021 21.7253 0.510817 21.8389C0.696612 21.9524 0.911921 22.0082 1.12941 21.999H11.0155C13.9288 21.999 16.7227 20.8402 18.7827 18.7773C20.8427 16.7145 22 13.9168 22 10.9995C22 8.08226 20.8427 5.28449 18.7827 3.22168C16.7227 1.15887 13.9288 0 11.0155 0ZM11.0155 19.7991H3.77668L4.79824 18.7762C5.00283 18.5701 5.11766 18.2913 5.11766 18.0007C5.11766 17.7101 5.00283 17.4313 4.79824 17.2252C3.35991 15.7865 2.46422 13.893 2.26377 11.8671C2.06333 9.84132 2.57052 7.80856 3.69894 6.1152C4.82736 4.42185 6.5072 3.17265 8.45226 2.58046C10.3973 1.98826 12.4873 2.08969 14.366 2.86748C16.2447 3.64526 17.7961 5.05128 18.7557 6.84598C19.7152 8.64068 20.0237 10.713 19.6286 12.7099C19.2334 14.7069 18.159 16.5048 16.5885 17.7975C15.018 19.0901 13.0485 19.7975 11.0155 19.7991ZM14.3108 9.89956H12.1139V7.69966C12.1139 7.40793 11.9982 7.12816 11.7922 6.92188C11.5862 6.7156 11.3068 6.59971 11.0155 6.59971C10.7242 6.59971 10.4448 6.7156 10.2388 6.92188C10.0328 7.12816 9.91703 7.40793 9.91703 7.69966V9.89956H7.72012C7.4288 9.89956 7.1494 10.0154 6.9434 10.2217C6.7374 10.428 6.62167 10.7078 6.62167 10.9995C6.62167 11.2912 6.7374 11.571 6.9434 11.7773C7.1494 11.9836 7.4288 12.0995 7.72012 12.0995H9.91703V14.2994C9.91703 14.5911 10.0328 14.8709 10.2388 15.0771C10.4448 15.2834 10.7242 15.3993 11.0155 15.3993C11.3068 15.3993 11.5862 15.2834 11.7922 15.0771C11.9982 14.8709 12.1139 14.5911 12.1139 14.2994V12.0995H14.3108C14.6022 12.0995 14.8816 11.9836 15.0876 11.7773C15.2936 11.571 15.4093 11.2912 15.4093 10.9995C15.4093 10.7078 15.2936 10.428 15.0876 10.2217C14.8816 10.0154 14.6022 9.89956 14.3108 9.89956Z" fill="black"/>
        </svg>
      </div>

      {/* Bottom Menu Items */}
      <div className="absolute bottom-8 left-0 right-0">
        {/* Menu Items */}
        <div className="flex flex-col gap-2 items-center">
          {menuItems.map((item) => (
            <motion.button
              key={item.id}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              className={`
                relative w-[37px] h-[37px] rounded-lg transition-all flex items-center justify-center
                ${activeItem === item.id 
                  ? 'bg-blue-50 text-blue-600' 
                  : 'text-gray-600 hover:bg-gray-50'
                }
              `}
              title={item.label}
            >
              <item.icon size={20} strokeWidth={1.5} />
            </motion.button>
          ))}
        </div>

        {/* Profile Circle */}
        <div className="mt-6 flex justify-center">
          <div className="w-9 h-9 rounded-full bg-[#6C56F3] flex items-center justify-center">
            <span className="text-white text-sm font-semibold">CT</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;