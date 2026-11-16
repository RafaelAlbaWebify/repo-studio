'use strict';
/* A strictly bounded CSSOM renderer. Repo Studio's CSP intentionally forbids
   inline style attributes; use rules inserted into its same-origin CSS file. */
const rsStyle = (() => {
  const rules = new Map();
  let serial = 0;
  const patterns = {
    'width': /^(?:0|(?:\d{1,3})(?:\.\d{1,17})?%)$/,
    'padding-left': /^\d{1,4}px$/,
    'color': /^(?:#[0-9a-fA-F]{6}|)$/,
    'background': /^(?:#[0-9a-fA-F]{6}|conic-gradient\([#0-9a-fA-F.,%\s-]+\))$/
  };
  return (node, property, input) => {
    if (!(node instanceof Element) || !Object.hasOwn(patterns, property)) throw Error('Invalid style target');
    const value = String(input);
    if (!patterns[property].test(value) || value.length > 350) throw Error('Invalid style value');
    const attr = 'data-rs-css-' + property.replace(/[^a-z]/g,'');
    if (value === '') { node.removeAttribute(attr); return; }
    const key = property + '\0' + value;
    let selector = rules.get(key);
    if (!selector) {
      if (serial >= 2500) throw Error('Too many CSS display states');
      const sheet = [...document.styleSheets].find(s => s.href && new URL(s.href).pathname === '/style.css');
      if (!sheet) throw Error('Local stylesheet unavailable');
      selector = 'rsdyn' + (++serial);
      sheet.insertRule(`[${attr}="${selector}"]{${property}:${value}}`, sheet.cssRules.length);
      rules.set(key, selector);
    }
    node.setAttribute(attr, selector);
  };
})();
