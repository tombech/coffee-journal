import React from 'react';
import { Link } from 'react-router-dom';

function SettingsCard({ title, description, icon, linkTo, iconAlt = '' }) {
  return (
    <Link to={linkTo} style={{ textDecoration: 'none' }}>
      <div style={{
        border: '1px solid #ddd',
        borderRadius: '8px',
        padding: '20px',
        margin: '10px',
        textAlign: 'center',
        backgroundColor: '#f9f9f9',
        cursor: 'pointer',
        transition: 'background-color 0.2s',
        minHeight: '150px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center'
      }}
      onMouseEnter={(e) => e.target.style.backgroundColor = '#f0f0f0'}
      onMouseLeave={(e) => e.target.style.backgroundColor = '#f9f9f9'}
      >
        {icon && (
          <img 
            src={icon} 
            alt={iconAlt} 
            style={{ width: '48px', height: '48px', marginBottom: '10px' }}
          />
        )}
        <h3 style={{ margin: '10px 0', color: '#333' }}>{title}</h3>
        <p style={{ margin: '0', color: '#666', fontSize: '14px' }}>{description}</p>
      </div>
    </Link>
  );
}

function Settings() {
  return (
    <div>
      <h2>Settings</h2>
      <p>Manage your coffee journal configuration and data.</p>
      
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
        gap: '15px',
        marginTop: '30px'
      }}>
        <SettingsCard
          title="Products"
          description="Manage your coffee products and batches"
          icon="/Roasted_coffee_beans.jpg"
          iconAlt="Coffee beans"
          linkTo="/products"
        />
        
        <SettingsCard
          title="Brew Methods"
          description="Configure brewing methods (V60, French Press, etc.)"
          icon="/coffee-recipe.png"
          iconAlt="Brew methods"
          linkTo="/settings/brew-methods"
        />
        
        <SettingsCard
          title="Recipes"
          description="Manage your brewing recipes and techniques"
          icon="/coffee-recipe.png"
          iconAlt="Recipes"
          linkTo="/settings/recipes"
        />
        
        <SettingsCard
          title="Bean Types"
          description="Configure coffee bean types and varieties"
          icon="/coffee-bean-brown.png"
          iconAlt="Bean types"
          linkTo="/settings/bean-types"
        />
        
        <SettingsCard
          title="Roasters"
          description="Manage coffee roaster information"
          icon="/coffee-beans.png"
          iconAlt="Roasters"
          linkTo="/settings/roasters"
        />
        
        <SettingsCard
          title="Countries"
          description="Configure coffee origin countries and regions"
          icon="/coffee-bean-white.png"
          iconAlt="Countries"
          linkTo="/settings/countries"
        />
        
        <SettingsCard
          title="Grinders"
          description="Manage coffee grinder equipment"
          icon="/beanconqueror-scale-outline.svg"
          iconAlt="Grinders"
          linkTo="/settings/grinders"
        />
        
        <SettingsCard
          title="Filters"
          description="Configure coffee filter types"
          icon="/coffee-bean-white.png"
          iconAlt="Filters"
          linkTo="/settings/filters"
        />
        
        <SettingsCard
          title="Kettles"
          description="Manage kettle equipment"
          icon="/kettle.png"
          iconAlt="Kettles"
          linkTo="/settings/kettles"
        />
        
        <SettingsCard
          title="Scales"
          description="Configure scale equipment"
          icon="/beanconqueror-scale-outline.svg"
          iconAlt="Scales"
          linkTo="/settings/scales"
        />
        
        <SettingsCard
          title="Decaf Methods"
          description="Manage decaffeination methods"
          icon="/coffee-bean-white.png"
          iconAlt="Decaf Methods"
          linkTo="/settings/decaf-methods"
        />
      </div>
    </div>
  );
}

export default Settings;