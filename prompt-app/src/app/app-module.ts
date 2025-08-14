import { NgModule, provideBrowserGlobalErrorListeners } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import {HTTP_INTERCEPTORS} from '@angular/common/http';
import { AppRoutingModule} from './app-routing-module';
import { App } from './app';
import { Login } from './pages/login/login';
import { Register } from './pages/register/register';
import {FormsModule, ReactiveFormsModule} from '@angular/forms';
import { Dashboard } from './pages/dashboard/dashboard';
import { Prompts } from './pages/prompts/prompts';
import { PromptDetail } from './pages/prompt-detail/prompt-detail';
import {CommonModule} from '@angular/common';
import { PromptAdd } from './pages/prompt-add/prompt-add';
import { HttpClientModule } from '@angular/common/http';
import {TokenInterceptorService} from './services/token-interceptor';
import { Header } from './layout/header/header';
import {MatIcon, MatIconModule} from '@angular/material/icon';
import {MatToolbarModule} from '@angular/material/toolbar';
import {MatCardModule} from '@angular/material/card';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatInputModule} from '@angular/material/input';
import {MatButtonModule} from '@angular/material/button';
import { Profile } from './pages/profile/profile';
import {MatProgressSpinner} from '@angular/material/progress-spinner';
import { FavoritePrompts } from './pages/favorite-prompts/favorite-prompts';
import {MatCheckbox} from '@angular/material/checkbox';
import { PromptCard } from './components/prompt-card/prompt-card';
import { AdminPanel } from './pages/admin-panel/admin-panel';
import {MatTooltipModule} from '@angular/material/tooltip';
import {MatTabsModule} from '@angular/material/tabs';
import {MatTableModule} from '@angular/material/table';
import {MatChipsModule} from '@angular/material/chips';
import {MatAutocompleteModule} from '@angular/material/autocomplete';
import {MatOptionModule} from '@angular/material/core';
import { MyPrompts } from './pages/my-prompts/my-prompts';
import { Search } from './pages/search/search';
import {MatDivider} from '@angular/material/divider';
import {MatPaginator} from '@angular/material/paginator';
import { TotpVerification } from './pages/totp-verification/totp-verification';
import { Footer } from './layout/footer/footer';


@NgModule({
  declarations: [
    App,
    Login,
    Register,
    Dashboard,
    Prompts,
    PromptDetail,
    PromptAdd,
    Header,
    Profile,
    FavoritePrompts,
    PromptCard,
    AdminPanel,
    MyPrompts,
    Search,
    TotpVerification,
    Footer,


  ],
    imports: [
        BrowserModule,
        AppRoutingModule,
        ReactiveFormsModule,
        FormsModule,
        CommonModule,
        HttpClientModule,
        MatIconModule,
        MatToolbarModule,
        MatCardModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule,
        MatProgressSpinner,
        MatTooltipModule,
        MatTabsModule,
        MatTableModule,
        MatCheckbox,
        MatChipsModule,
        MatAutocompleteModule,
        MatOptionModule,
        MatDivider,
        MatPaginator,
    ],
  providers: [
    provideBrowserGlobalErrorListeners(),
    {
      provide: HTTP_INTERCEPTORS,
      useClass: TokenInterceptorService,
      multi: true
    }



  ],

  bootstrap: [App]
})
  export class AppModule {


}
