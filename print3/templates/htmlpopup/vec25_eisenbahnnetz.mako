<%inherit file="base.mako"/>

<%def name="table_body(c,lang)">
    <tr><td class="cell-left">${_('laenge_strecke_m')}</td><td>${int(round(c['attributes']['length'])) or '-'} m</td></tr>
</%def>
