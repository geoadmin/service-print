<%inherit file="base.mako"/>

<%def name="table_body(c, lang)">

<% c['stable_id'] = True %>
    <tr><td class="cell-left">${_('ch.bfe.abgeltung-wasserkraftnutzung.name')}</td>                        <td>${c['attributes']['name']}</td></tr>
    <tr><td class="cell-left">${_('tt_ch.bfe.abgeltung-wasserkraftnutzung_objectnumber')}</td>                <td>${c['featureId'] or '-'}</td></tr>
    <tr><td class="cell-left">${_('tt_ch.bfe.abgeltung-wasserkraftnutzung_area')}</td>                        <td>${c['attributes']['area'] or '-'}</td></tr>
    <tr><td class="cell-left">${_('tt_ch.bfe.abgeltung-wasserkraftnutzung_perimeter')}</td>                   <td>${c['attributes']['perimeter'] or '-'}</td></tr>
    <tr><td class="cell-left">${_('tt_ch.bfe.abgeltung-wasserkraftnutzung_startprotectioncommitment')}</td>   <td>${h.parse_date_string(c['attributes']['startprotectioncommitment'])}</td></tr>
    <tr><td class="cell-left">${_('tt_ch.bfe.abgeltung-wasserkraftnutzung_endprotectioncommitment')}</td>     <td>${h.parse_date_string(c['attributes']['endprotectioncommitment'])}</td></tr>
</%def>
