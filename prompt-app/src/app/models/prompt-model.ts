import {Label} from './label-model';

export interface Prompt {
  id: number;
  content: string;
  is_public: boolean;
  user_id: number;
  author_username: string;
  no_of_likes: number;
  created_at: string;
  updated_at: string;
  is_liked_by_user: boolean;
  labels: Label[];

}
