import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Home from './components/Home';
import ProductList from './components/ProductList';
import ProductDetail from './components/ProductDetail';
import ProductForm from './components/ProductForm';
import BrewSessionList from './components/BrewSessionList';
import BrewSessionDetail from './components/BrewSessionDetail';
import BrewSessionForm from './components/BrewSessionForm';
import BrewSessionNew from './components/BrewSessionNew';
import BatchDetail from './components/BatchDetail';
import Settings from './components/Settings';
import { ShotList, ShotDetail, ShotForm } from './components/shots';
import { ShotSessionList, ShotSessionDetail, ShotSessionForm } from './components/shotSessions';
import BrewMethodManager from './components/lookup/BrewMethodManager';
import RecipeManager from './components/lookup/RecipeManager';
import BeanTypeManager from './components/lookup/BeanTypeManager';
import RoasterManager from './components/lookup/RoasterManager';
import RoasterDetail from './components/RoasterDetail';
import CountryManager from './components/lookup/CountryManager';
import CountryEdit from './components/lookup/CountryEdit';
import GrinderManager from './components/lookup/GrinderManager';
import GrinderDetail from './components/GrinderDetail';
import FilterManager from './components/lookup/FilterManager';
import KettleManager from './components/lookup/KettleManager';
import ScaleManager from './components/lookup/ScaleManager';
import DecafMethodManager from './components/lookup/DecafMethodManager';
import BrewerManager from './components/lookup/BrewerManager';
import PortafilterManager from './components/lookup/PortafilterManager';
import BasketManager from './components/lookup/BasketManager';
import TamperManager from './components/lookup/TamperManager';
import WDTToolManager from './components/lookup/WDTToolManager';
import LevelingToolManager from './components/lookup/LevelingToolManager';
import LookupDetail from './components/LookupDetail';
import { ToastProvider } from './components/Toast';
import VersionFooter from './components/VersionFooter';
import './App.css'; // Import the CSS file

function App() {
  return (
    <ToastProvider>
      <Router>
        <div className="App">
          <header className="App-header">
            <h1>My Coffee Journal</h1>
            <nav>
              <ul>
                <li><Link to="/">Home</Link></li>
                <li><Link to="/brew-sessions">All brews</Link></li>
                <li><Link to="/shots">All shots</Link></li>
                <li><Link to="/shot-sessions">Shot sessions</Link></li>
                <li><Link to="/settings">Settings</Link></li>
              </ul>
            </nav>
          </header>

          <main className="App-main" data-testid="app-main">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/products" element={<ProductList />} />
              <Route path="/products/new" element={<ProductForm />} />
              <Route path="/products/edit/:id" element={<ProductForm />} /> {/* For editing existing product */}
              <Route path="/products/:id" element={<ProductDetail />} />
              <Route path="/brew-sessions" element={<BrewSessionList />} />
              <Route path="/brew-sessions/new" element={<BrewSessionNew />} />
              <Route path="/brew-sessions/:id" element={<BrewSessionDetail />} />
              <Route path="/brew-sessions/:id/edit" element={<BrewSessionForm />} />
              <Route path="/shots" element={<ShotList />} />
              <Route path="/shots/new" element={<ShotForm />} />
              <Route path="/shots/:id" element={<ShotDetail />} />
              <Route path="/shots/:id/edit" element={<ShotForm />} />
              <Route path="/shot-sessions" element={<ShotSessionList />} />
              <Route path="/shot-sessions/:id" element={<ShotSessionDetail />} />
              <Route path="/shot-sessions/:id/edit" element={<ShotSessionForm />} />
              <Route path="/batches/:id" element={<BatchDetail />} />
              <Route path="/batches/:id/edit" element={<BatchDetail />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/settings/brew-methods" element={<BrewMethodManager />} />
              <Route path="/settings/recipes" element={<RecipeManager />} />
              <Route path="/settings/bean-types" element={<BeanTypeManager />} />
              <Route path="/settings/roasters" element={<RoasterManager />} />
              <Route path="/settings/countries" element={<CountryManager />} />
              <Route path="/settings/countries/:id/edit" element={<CountryEdit />} />
              <Route path="/settings/grinders" element={<GrinderManager />} />
              <Route path="/settings/filters" element={<FilterManager />} />
              <Route path="/settings/kettles" element={<KettleManager />} />
              <Route path="/settings/scales" element={<ScaleManager />} />
              <Route path="/settings/decaf-methods" element={<DecafMethodManager />} />
              <Route path="/settings/brewers" element={<BrewerManager />} />
              <Route path="/settings/portafilters" element={<PortafilterManager />} />
              <Route path="/settings/baskets" element={<BasketManager />} />
              <Route path="/settings/tampers" element={<TamperManager />} />
              <Route path="/settings/wdt-tools" element={<WDTToolManager />} />
              <Route path="/settings/leveling-tools" element={<LevelingToolManager />} />
              
              {/* Detail pages for lookups */}
              <Route path="/roasters/:id" element={<RoasterDetail />} />
              <Route path="/grinders/:id" element={<GrinderDetail />} />
              <Route path="/brew-methods/:id" element={<LookupDetail type="brew_methods" singularName="Brew Method" pluralName="Brew Methods" />} />
              <Route path="/recipes/:id" element={<LookupDetail type="recipes" singularName="Recipe" pluralName="Recipes" />} />
              <Route path="/bean-types/:id" element={<LookupDetail type="bean_types" singularName="Bean Type" pluralName="Bean Types" />} />
              <Route path="/countries/:id" element={<LookupDetail type="countries" singularName="Country" pluralName="Countries" />} />
              <Route path="/filters/:id" element={<LookupDetail type="filters" singularName="Filter" pluralName="Filters" />} />
              <Route path="/kettles/:id" element={<LookupDetail type="kettles" singularName="Kettle" pluralName="Kettles" />} />
              <Route path="/scales/:id" element={<LookupDetail type="scales" singularName="Scale" pluralName="Scales" />} />
              <Route path="/decaf-methods/:id" element={<LookupDetail type="decaf_methods" singularName="Decaf Method" pluralName="Decaf Methods" />} />
              <Route path="/brewers/:id" element={<LookupDetail type="brewers" singularName="Brewer" pluralName="Brewers" />} />
              <Route path="/portafilters/:id" element={<LookupDetail type="portafilters" singularName="Portafilter" pluralName="Portafilters" />} />
              <Route path="/baskets/:id" element={<LookupDetail type="baskets" singularName="Basket" pluralName="Baskets" />} />
              <Route path="/tampers/:id" element={<LookupDetail type="tampers" singularName="Tamper" pluralName="Tampers" />} />
              <Route path="/wdt_tools/:id" element={<LookupDetail type="wdt_tools" singularName="WDT Tool" pluralName="WDT Tools" />} />
              <Route path="/leveling_tools/:id" element={<LookupDetail type="leveling_tools" singularName="Leveling Tool" pluralName="Leveling Tools" />} />
            </Routes>
          </main>
          <VersionFooter />
        </div>
      </Router>
    </ToastProvider>
  );
}

export default App;