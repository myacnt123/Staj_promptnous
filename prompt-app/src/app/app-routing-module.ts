import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { Login } from './pages/login/login';
import { Register } from './pages/register/register';
import {Dashboard} from './pages/dashboard/dashboard';
import {Prompts} from './pages/prompts/prompts';
import {PromptDetail} from './pages/prompt-detail/prompt-detail';
import {PromptAdd} from './pages/prompt-add/prompt-add';
import {Profile} from './pages/profile/profile';
import {AuthGuard} from './guards/auth-guard';
import {FavoritePrompts} from './pages/favorite-prompts/favorite-prompts';
import {AdminGuard} from './guards/admin-guard';
import {AdminPanel} from './pages/admin-panel/admin-panel';
import {MyPrompts} from './pages/my-prompts/my-prompts';
import {Search} from './pages/search/search';

const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: Login },
  { path: 'register', component: Register },
  { path: 'dashboard', component: Dashboard },
  { path: 'prompts', component: Prompts },
  { path: 'prompt-detail/:id', component: PromptDetail },
  { path: 'prompt-add', component: PromptAdd },
  { path: 'profile', component: Profile, canActivate: [AuthGuard] },
  {path: 'favorites', component: FavoritePrompts, canActivate: [AuthGuard]},
  {path: 'admin-panel', component: AdminPanel, canActivate: [AdminGuard]},
  { path: 'my-prompts', component: MyPrompts },
  { path: 'search', component: Search },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
