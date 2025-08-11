// src/app/models/comment-model.ts

export interface Comment {
  comment_id: number;
  content: string;
  user_id: number;
  author_username: string;
  prompt_id: number;
  created_at: string;

}
