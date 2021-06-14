import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import PrimeVue from 'primevue/config';
import Dropdown from 'primevue/dropdown';

import 'primevue/resources/themes/saga-blue/theme.css'       //theme
import 'primevue/resources/primevue.min.css'                //core css
import 'primeicons/primeicons.css'                          //icons
import 'primeflex/primeflex.css';
import InputText from 'primevue/inputtext';
import Button from 'primevue/button';
import FileUpload from 'primevue/fileupload';
import InputNumber from 'primevue/inputnumber';
import ScrollPanel from 'primevue/scrollpanel';
import OverlayPanel from 'primevue/overlaypanel';
import Splitter from 'primevue/splitter';
import SplitterPanel from 'primevue/splitterpanel';
import Chart from 'primevue/chart';
import Fieldset from 'primevue/fieldset';
import Tag from 'primevue/tag';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import ProgressBar from 'primevue/progressbar';
import ToastService from 'primevue/toastservice';


const app = createApp(App)
app.use(router).mount('#app')
app.use(PrimeVue);
app.use(ToastService);
app.component('Dropdown', Dropdown);
app.component('InputText', InputText);
app.component('Button', Button);
app.component('FileUpload', FileUpload);
app.component('InputNumber', InputNumber);
app.component('ScrollPanel', ScrollPanel);
app.component('OverlayPanel', OverlayPanel);
app.component('Splitter', Splitter);
app.component('SplitterPanel', SplitterPanel);
app.component('Chart', Chart);
app.component('Fieldset', Fieldset);
app.component('Tag', Tag);
app.component('DataTable', DataTable);
app.component('Column', Column);
app.component('ProgressBar', ProgressBar);

